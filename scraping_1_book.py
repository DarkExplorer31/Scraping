import requests
from bs4 import BeautifulSoup as bs
import csv

product_page_url = 'http://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html'

response = requests.get(product_page_url)

#Informations à avoir
if response.ok:
    all_titles = ['URL','UPC','Title','Price (incl. tax)','Price (excl. tax)','Availability','Product Description','Category','Rating','Image URL'] #Liste des Titres
    all_infos = [] #Liste des Infos tirées du site
    #Première info: L'URL
    all_infos.append(product_page_url)
    #Paramétrage de BeautifulSoup
    soup = bs(response.text, features='html.parser') 
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
    review_rating = soup.find('p',{'class':'star-rating One'})
    review_rating = review_rating['class']
    review_rating = str(review_rating[1])
    all_rated = {'One':1,'Two':2,'Three':3,'Four':4,'Five':1} 
    if review_rating in all_rated:#Transformer en int()
        review_rating = all_rated[review_rating]
    all_infos.append(review_rating)
    #L'url de l'image
    image_url = soup.find('img')
    all_infos.append(image_url['src'])
    with open('result.csv','w') as result:
        writer = csv.writer(result)
        writer.writerow(all_titles)
        writer.writerow(all_infos)