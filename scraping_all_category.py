import requests, csv, os, time
from bs4 import BeautifulSoup as bs
from urllib.request import urlretrieve
from urllib.parse import urljoin

#Definition des fonctions utiles
def search_product(url_product):
    """Fonction qui cherche les informations par livre"""
    requests_product = requests.get(url_product)
    if requests_product.ok:
        all_infos = [] #Liste des Infos tirées du livre traité
        #Première info: L'URL
        all_infos.append(url_product)
        #Paramétrage de BeautifulSoup
        soup = bs(requests_product.text, features='html.parser') 
        #Deuxième info: UPC
        source_table = soup.find_all('td')
        universal_product_code = source_table[0]
        all_infos.append(universal_product_code.text)
        #Troisième info: Le Titre du livre
        title = soup.find('h1')
        all_infos.append(title.text)
        #Quatrième Info: Prix incluant la tax
        price_including_tax = source_table[3].text
        price_including_tax = price_including_tax.replace('Â£','')
        all_infos.append(price_including_tax)
        #Cinquième Info: Prix excluant la tax
        price_excluding_tax = source_table[2].text
        price_excluding_tax = price_excluding_tax.replace('Â£','')
        all_infos.append(price_excluding_tax)
        #Sixième Info: Nombre Disponible
        number_available = source_table[5].text
        all_infos.append(number_available)
        #Description du Produit
        product_description = soup.find('p',{'class':None})
        if product_description == None:
            product_description = 'N/A'
            all_infos.append(product_description)
        else:
            all_infos.append(product_description.text)
        #Catégorie
        source_link = soup.find_all('a')
        category = source_link[3].text
        all_infos.append(category)
        #La note reçu
        all_rated = {'One':1,'Two':2,'Three':3,'Four':4,'Five':5}
        review_rating = soup.find('p',{"class":"star-rating"})
        review_rating = review_rating['class']
        review_rating = review_rating[1]
        if review_rating in all_rated:
            review_rating = all_rated[review_rating]
            all_infos.append(review_rating)
        #L'url de l'image
        image_url = soup.find('img')
        all_infos.append(image_url['src'])
        return all_infos
    else:
        raise ValueError("L'Url n'est pas bon")

def download_img(repo_receiver,title_img,url):
    """Fonction qui enregistre les images"""
    title_img = title_img.replace(' ', '_')
    final_path = repo_receiver + title_img.capitalize() + '.jpg'
    urlretrieve(url,final_path)
    
def search_category(link_category, title_category, page_url):
    """Fonction qui cherche les infos pour toutes les categories et les enregistres"""
    #Définition des variables
    all_titles = ['URL','UPC','Title','Price (incl. tax)','Price (excl. tax)','Availability','Product Description','Category','Rating','Image URL'] #Liste des Titres
    infos_by_category = [] #Liste des infos tirées de tout les livres
    title_category = title_category.replace(' ', '_')
    file_reveiver = "Data/{}".format(title_category)
    
    #Paramétrage des fichiers de réception
    data_folder_exist = os.path.exists('Data')
    test_lien = os.path.exists(file_reveiver) #On vérifie le lien des dossiers de dépose des infos et des images
    if data_folder_exist is False:
        os.mkdir('Data')
    if test_lien is False:
        os.mkdir(file_reveiver) #Si les fichiers n'existe pas, on les créés

    #On lance la fonction pour trouver les infos de tout les livres de la catégorie en argument:
    response = requests.get(link_category) #On prend les premier paramètre fournis: le lien vers la première page de la catégorie
    if response.ok: #Si le lien est correct
        soup = bs(response.text, features='html.parser') #On paramètre 'BeautifulSoup' sur ce lien
        nb_page = soup.find('li',{'class':'current'}) #On cherche si il y a plus d'une page
        try:
            nb_page = nb_page.text
        except AttributeError: #Si on as qu'une page
            nb_page = 1
        if nb_page != 1: #Si on as plus d'une page
            nb_page = nb_page.split()
            nb_page = int(nb_page[3])#On récupère le nombre de page
        for page in range(1,nb_page+1): #On fait une boucle par page
            if page == 2:
                link_category = link_category.replace('index.html','page-2.html')
            elif page > 2:
                previous_page = 'page-{}.html'.format(page - 1)
                link_category = link_category.replace(previous_page,'page-{}.html'.format(page))
                print(link_category)
            response = requests.get(link_category) #On fait une requête 'GET' sur chaque lien de page
            soup = bs(response.text, features='html.parser') #On reparamètre 'BeautifulSoup' pour chaque page de la catégorie
            if response.ok: #Si le lien répond
                url_books = soup.find_all('h3',{'class':None}) #On cherche les URLs de chaque livre de la catégorie
                for url in url_books: #On ajoute les URLs trouvées 
                    a = url.find('a')
                    book_url = a['href']
                    book_url = urljoin(link_category,book_url) #On recréer le lien fourni
                    book_infos = search_product(book_url) #On prend les informations de chaque livre
                    infos_by_category.append(book_infos)
                    img_url = book_infos[9] #Maintenant qu'on as les informations, on récupère les images
                    img_url = urljoin(page_url,img_url) #on remplace le lien fourni par un lien valide
                    download_img('{}/'.format(file_reveiver),book_infos[2],img_url) #On récupère respectivement le titre du livre et l'URL de l'image, que l'on passe à notre fonction de téléchargement
        with open('{}/result-{}.csv'.format(file_reveiver,title_category),'w', encoding='utf-8') as result: #On ecrit les fichier '.csv' après avoir récuperer toutes les informations
            writer = csv.writer(result)
            writer.writerow(all_titles) #D'abord les titres, puis les informations pour chaque livre
            for element in infos_by_category: #A la fin de l'analyse de chaque catégorie, on écrit le '.csv' et on remet la liste 'infos_by_category' à zero
                writer.writerow(element)
        print("Categorie traité: {}".format(title_category))
        time.sleep(1) #On attend pour ne pas surchager de connexion

page_url = 'http://books.toscrape.com/'
response = requests.get(page_url)
if response.ok: #Si le lien vers la page est bon
    soup = bs(response.text, features='html.parser')
    url_first_page = soup.find('ul',{'class':None})
    urls_category = url_first_page.find_all('a') #On trie toutes les 'a' pour n'avoir que les 'a' des categories
    for link in urls_category: #On ajoute les URLs trouvées 
        link_category = page_url + link['href']
        title_category = link.text.strip() #On récupère les titres des catégories
        infos_by_category = search_category(link_category,title_category,page_url)

