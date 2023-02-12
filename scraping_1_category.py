import requests, csv
from bs4 import BeautifulSoup as bs

links_url = []
all_titles = ['URL','UPC','Title','Price (incl. tax)','Price (excl. tax)','Availability','Product Description','Category','Rating','Image URL'] #Liste des Titres
result_category = [] #Liste des infos tirées de tout les livres 

def Search(url_product):
    """Fonction qui cherche les informations par livres"""
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
        all_infos.append(product_description.text)
        #Catégorie
        source_link = soup.find_all('a')
        category = source_link[3].text
        all_infos.append(category)
        #La note reçu
        all_rated = {'One':1,'Two':2,'Three':3,'Four':4,'Five':1}
        for score in all_rated: #On cherche la note du livre traiter, puique le nom de la class en dépend
            review_rating = soup.find('p',{'class':'star-rating {}'.format(score)})
            if review_rating == None:
                pass
            else:
                review_rating = review_rating['class']
                review_rating = str(review_rating[1])
                if review_rating in all_rated:#Transformer en int()
                    review_rating = all_rated[review_rating]
                all_infos.append(review_rating)
        #L'url de l'image
        image_url = soup.find('img')
        all_infos.append(image_url['src'])
        return all_infos
    else:
        return("L'Url n'est pas bon")

page_url_category = 'http://books.toscrape.com/catalogue/category/books/historical-fiction_4/page-1.html' #url de la catégorie "historical-fiction" page 1
response = requests.get(page_url_category)
if response.ok:
    soup = bs(response.text, features='html.parser')
    next = soup.find('li',{'class':'current'})
    nb_page = next.text.strip()
    if len(nb_page) == 11: #On cherche le nombre de page
        nb_page = nb_page[-1:]
    else:
        nb_page = nb_page[-2:]
    try:
        nb_page = int(nb_page)
    except ValueError:
        nb_page = int(nb_page)
    nb_page += 1
    for page in range(1,nb_page): #On fait une boucle par page
        url_category = 'http://books.toscrape.com/catalogue/category/books/historical-fiction_4/page-{}.html'.format(page) #On fait une boucle pour avoir toutes les URLs de la catégorie
        response = requests.get(url_category)
        soup = bs(response.text, features='html.parser')
        if response.ok:
            urls = soup.find_all('h3',{'class':None})
            for url in urls: #On ajoute les URLs trouvées 
                a = url.find('a')
                link_url = a['href']
                link_url = link_url.replace('../../../','http://books.toscrape.com/catalogue/')
                links_url.append(link_url) #On récupère les urls de chaque livre dans la catégorie, et on l'ajoute dans une liste
            for link in links_url:
                infos = Search(link)
                result_category.append(infos) #On ajoute les titres puis les resultats, ligne par lignes
                with open('Data/result.csv','w', encoding='utf-8') as result: 
                    writer = csv.writer(result)
                    writer.writerow(all_titles)
                    for info in result_category:
                        writer.writerow(info)
