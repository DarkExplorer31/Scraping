import requests
import csv
import os
import time
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
from urllib.request import urlretrieve
from urllib.parse import urljoin

absolute_link = os.path.abspath(__file__)
path_to_file = os.path.dirname(absolute_link)
os.chdir(path_to_file)


def response_control(response_status):
    if response_status < 100:
        raise AttributeError(
            "Le server à reçu la requête mais la requête n'est pas un succès"
        )
    elif response_status >= 200 and response_status < 300:
        return response_status
    elif response_status >= 300 and response_status < 400:
        raise AttributeError("Le lien a subi une redirection")
    if response_status >= 400 and response_status < 500:
        raise AttributeError(
            "La page demandée ne répond plus, vérifiez "
            + "l'URL utilisé ou limité la quantité de requête"
        )
    else:
        raise AttributeError(
            "La requête au site a échoué, vérifiez votre connexion"
            + " internet ou que le serveur est encore existant"
        )


def search_product(url_product):
    response = requests.get(url_product)
    response_control(response.status_code)
    all_infos = []
    all_infos.append(url_product)
    response_encode = response.text
    response_encode = response_encode.encode("ISO-8859-1")
    dammit = UnicodeDammit(response_encode, ["utf-8", "ISO-8859-1"]).unicode_markup
    soup = BeautifulSoup(dammit, features="html.parser")
    source_table = soup.find_all("td")
    universal_product_code = source_table[0]
    all_infos.append(universal_product_code.text)
    title = soup.find("h1")
    all_infos.append(title.text)
    price_including_tax = source_table[3].text
    all_infos.append(price_including_tax)
    price_excluding_tax = source_table[2].text
    all_infos.append(price_excluding_tax)
    availability = source_table[5].text
    availability = availability.split()
    number_available = availability[2]
    all_infos.append(number_available.strip("("))
    product_description = soup.find("p", {"class": None})
    if not product_description:
        product_description = "N/A"
        all_infos.append(product_description)
    else:
        product_description = product_description.text
        all_infos.append(product_description)
    source_link = soup.find_all("a")
    category = source_link[3].text
    all_infos.append(category)
    all_rated = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    review_rating = soup.find("p", {"class": "star-rating"})
    review_rating = review_rating["class"]
    review_rating = review_rating[1]
    if review_rating in all_rated:
        review_rating = all_rated[review_rating]
        all_infos.append(review_rating)
    image_url = soup.find("img")
    all_infos.append(image_url["src"])
    return all_infos


def download_img(repo_receiver, title_img, url):
    title_img = title_img.replace(" ", "_")
    final_path = repo_receiver + title_img.title() + ".png"
    img_download = urlretrieve(url, final_path)
    return img_download


def control_local_link(file_to_test):
    if os.path.exists("Data") is False:
        os.mkdir("Data")
    if os.path.exists(file_to_test) is False:
        os.mkdir(file_to_test)


def find_nb_page(page):
    page_element = page.find("li", {"class": "current"})
    if page_element is None:
        return 1
    else:
        pagination_text = page_element.text
        page_element = pagination_text.split()
        return int(pagination_text.split()[3])


def save_csv(file, title, to_save):
    all_titles = [
        "URL",
        "UPC",
        "Title",
        "Price (incl. tax)",
        "Price (excl. tax)",
        "Availability",
        "Product Description",
        "Category",
        "Rating",
        "Image URL",
    ]
    with open("{}/result-{}.csv".format(file, title), "w", encoding="utf-8") as result:
        writer = csv.writer(result)
        writer.writerow(all_titles)
        for element in to_save:
            writer.writerow(element)


def search_category(link_category, title_category, page_url):
    infos_by_category = []
    file_receiver = "Data/{}".format(title_category)
    control_local_link(file_receiver)
    response = requests.get(link_category)
    response_control(response.status_code)
    soup = BeautifulSoup(response.text, features="html.parser")
    nb_page = find_nb_page(soup)
    for page in range(1, nb_page + 1):
        if page == 2:
            link_category = link_category.replace("index.html", "page-2.html")
        elif page > 2:
            previous_page = "page-{}.html".format(page - 1)
            link_category = link_category.replace(
                previous_page, "page-{}.html".format(page)
            )
        response = requests.get(link_category)
        response_control(response.status_code)
        soup = BeautifulSoup(response.text, features="html.parser")
        url_books = soup.find_all("h3", {"class": None})
        for url in url_books:
            a = url.find("a")
            book_url = a["href"]
            book_url = urljoin(link_category, book_url)
            book_infos = search_product(book_url)
            infos_by_category.append(book_infos)
            img_url = book_infos[9]
            img_url = urljoin(page_url, img_url)
            book_title = book_infos[0]
            book_title = book_title.split("/")
            book_title = book_title[4]
            download_img("{}/".format(file_receiver), book_title, img_url)
    title_category = title_category.replace(" ", "_")
    save_csv(file_receiver, title_category, infos_by_category)
    time.sleep(1)
    return "Catégorie traitée: {}".format(title_category)


page_url = "http://books.toscrape.com/"
response = requests.get(page_url)
response_control(response.status_code)
soup = BeautifulSoup(response.text, features="html.parser")
url_first_page = soup.find("ul", {"class": None})
urls_category = url_first_page.find_all("a")
for link in urls_category:
    link_category = page_url + link["href"]
    title_category = link.text.strip()
    infos_by_category = search_category(link_category, title_category, page_url)
    print(infos_by_category)
