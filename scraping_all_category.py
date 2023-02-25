import requests, csv, os, time
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
from urllib.request import urlretrieve
from urllib.parse import urljoin

#On s'assure que le code s'execute dans le fichier où se trouve le code
absolute_link = os.path.abspath(__file__)
path_to_file = os.path.dirname(absolute_link)
os.chdir(path_to_file)

#Définition des fonctions utilisées
def search_product(url_product):
    """Fonction qui cherche les informations par livre, prend en paramètre uniquement le lien URL du livre"""
    response = requests.get(url_product)
    if not response.ok: #Si le lien n'est pas correct
        raise AttributeError("URL incorrect")
    all_infos = [] #Liste des Informations tirées du livre traité
    all_infos.append(url_product)
    response_encode = response.text
    response_encode = response_encode.encode("ISO-8859-1")
    dammit = UnicodeDammit(response_encode, ["utf-8","ISO-8859-1"]).unicode_markup 
    soup = BeautifulSoup(dammit, features='html.parser') 
    source_table = soup.find_all('td') #Nous recherchons toutes les informations des éléments '<td>' qui forment la description du livre
    #par exemple: '[<td>a22124811bfa8350</td>, <td>Books</td>, <td>£45.17</td>, <td>£45.17</td>, <td>£0.00</td>, <td>In stock (19 available)</td>, <td>0</td>]'
    universal_product_code = source_table[0] # Ici, nous retourne l'UPC par exemple: '<td>a22124811bfa8350</td>'
    all_infos.append(universal_product_code.text) 
    title = soup.find('h1')
    all_infos.append(title.text)
    price_including_tax = source_table[3].text #On va chercher le prix, par exemple: '£45.17'
    all_infos.append(price_including_tax)
    price_excluding_tax = source_table[2].text 
    all_infos.append(price_excluding_tax)
    availability = source_table[5].text #On cherche la disponibilité pour tirer le nombre disponible, par exemple: 'In stock (19 available)'
    availability = availability.split() #On divise la chaine de caractère pour garder le nombre: '['In', 'stock', '(19', 'available)']'
    number_available = availability[2] 
    all_infos.append(number_available.strip('('))
    product_description = soup.find('p',{'class':None})
    if product_description == None:
        product_description = 'N/A'
        all_infos.append(product_description)
    else:
        product_description = product_description.text
        all_infos.append(product_description)
    source_link = soup.find_all('a')
    category = source_link[3].text
    all_infos.append(category)
    all_rated = {'One':1,'Two':2,'Three':3,'Four':4,'Five':5}
    review_rating = soup.find('p',{"class":"star-rating"})
    review_rating = review_rating['class']
    review_rating = review_rating[1]
    if review_rating in all_rated:
        review_rating = all_rated[review_rating]
        all_infos.append(review_rating)
    image_url = soup.find('img')
    all_infos.append(image_url['src'])
    return all_infos 

def download_img(repo_receiver,title_img,url):
    """Fonction qui enregistre les images. Prend en paramètre le fichier de réception, le titre de l'image et son URL."""
    title_img = title_img.replace(' ', '_')
    final_path = repo_receiver + title_img.title() + '.png'
    img_download = urlretrieve(url,final_path)
    return img_download

def response_control(response_status):
    """Fonction qui control la réponse du site. Prend en paramètre le status de la réponse"""
    if response_status < 100:
        raise AttributeError("Le server à reçu la requête mais la requête n'est pas un succès")
    elif response_status >= 200 and response_status < 300:
        return response_status
    elif response_status >= 300 and response_status < 400:
        raise AttributeError("Le lien a subi une redirection")
    if response_status >= 400 and response_status < 500:
        raise AttributeError("La page demandée ne répond plus, vérifiez l'URL utilisé ou limité la quantité de requête")
    else: #Si le status est supérieur à 500
        raise AttributeError("La requête au site a échoué, vérifiez votre connexion internet ou que le serveur est encore existant")
    
def control_local_link(file_to_test):
    """Fonction qui vérifie la présence des fichiers de récéptions en local. Prend en paramètre le lien à essayer"""
    if os.path.exists('Data') is False:
        os.mkdir('Data')
    if os.path.exists(file_to_test) is False:
        os.mkdir(file_to_test)

def find_nb_page(page):
    """Fonction qui détermine le nombre de page à analyser. Prend en paramètre seulement l'URL de la page à analyser"""
    page_element = page.find('li',{'class':'current'}) #On cherche si il y a plus d'une page en prenant l'information de bas de page par exemple: 'Page 1 of 2'
    if page_element is None: 
        return 1
    else:
        pagination_text = page_element.text
        page_element = pagination_text.split()
        return int(pagination_text.split()[3])#On récupère le nombre de page

def save_csv(file,title,to_save):
    """Fonction qui enregistre les informations tirées. Prend en paramètre le repertoire de dépose, le titre du fichier et les données à écrire à l'intérieur"""
    all_titles = ['URL','UPC','Title','Price (incl. tax)','Price (excl. tax)','Availability','Product Description','Category','Rating','Image URL'] #Liste des Titres
    with open('{}/result-{}.csv'.format(file,title),'w', encoding='utf-8') as result: #On ecrit les fichier '.csv' après avoir récuperer toutes les informations
        writer = csv.writer(result)
        writer.writerow(all_titles) #D'abord les titres, puis les informations pour chaque livre
        for element in to_save: #A la fin de l'analyse de chaque catégorie, on écrit le fichier '.csv' et on remet la liste 'infos_by_category' à zéro
            writer.writerow(element)

def search_category(link_category, title_category, page_url):
    """Fonction qui cherche les informations pour toutes les categories.
    Prend en paramètre le lien d'une catégorie, le titre de celle-ci et son lien URL."""
    infos_by_category = [] #Liste des informations tirées de tout les livres
    file_receiver = "Data/{}".format(title_category)
    control_local_link(file_receiver) 
    response = requests.get(link_category) #On prend les premiers paramètres fournis: le lien vers la première page de la catégorie
    response_control(response.status_code) #On contrôle la response du site
    soup = BeautifulSoup(response.text, features='html.parser') #On paramètre 'BeautifulSoup' sur ce lien
    nb_page = find_nb_page(soup) #On utilise la fonction qui cherche le nombre de page
    for page in range(1,nb_page+1): 
        if page == 2:
            link_category = link_category.replace('index.html','page-2.html') #joindre l'url avec le complet 'page-{}'
        elif page > 2:
            previous_page = 'page-{}.html'.format(page - 1)
            link_category = link_category.replace(previous_page,'page-{}.html'.format(page))
        response = requests.get(link_category) #On fait une requête 'GET' sur chaque lien de page
        response_control(response.status_code)
        soup = BeautifulSoup(response.text, features='html.parser') #On reparamètre 'BeautifulSoup' pour chaque page de la catégorie
        url_books = soup.find_all('h3',{'class':None}) #On cherche les URLs de chaque livre de la catégorie
        for url in url_books: #On ajoute les URLs trouvées 
            a = url.find('a')
            book_url = a['href']
            book_url = urljoin(link_category,book_url) #On recréer le lien fourni
            book_infos = search_product(book_url) #On prend les informations de chaque livre
            infos_by_category.append(book_infos)
            img_url = book_infos[9] #Maintenant qu'on as les informations, on récupère les images
            img_url = urljoin(page_url,img_url) #on remplace le lien fourni par un lien valide
            book_title = book_infos[0]
            book_title = book_title.split('/')
            book_title = book_title[4]
            download_img('{}/'.format(file_receiver),book_title,img_url) #On récupère le titre du livre et l'URL de l'image, que l'on passe à notre fonction de téléchargement
    title_category = title_category.replace(' ', '_')
    save_csv(file_receiver,title_category,infos_by_category)
    time.sleep(1) #On attend pour ne pas surchargé de connexion
    return("Catégorie traitée: {}".format(title_category))

page_url = 'http://books.toscrape.com/'
response = requests.get(page_url)
response_control(response.status_code)
soup = BeautifulSoup(response.text, features='html.parser')
url_first_page = soup.find('ul',{'class':None})
urls_category = url_first_page.find_all('a') #On trie toutes les '<a>' pour n'avoir que les '<a>' des categories
for link in urls_category: #On ajoute les URLs de catégories trouvés 
    link_category = page_url + link['href']
    title_category = link.text.strip() #On récupère les titres des catégories
    infos_by_category = search_category(link_category,title_category,page_url)
    print(infos_by_category)

