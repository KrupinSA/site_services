from requests import Session, Request
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit
import os
from threading import current_thread
from zipfile import ZipFile, ZIP_DEFLATED
from shutil import rmtree


def get_page_content(session, page_url):
    response = session.get(page_url)
    response.raise_for_status
    return response.content
    
def get_script_files(soup, site_url):
    script_files = []
    for script in soup.find_all("script"):
        # Качаем только по относительным ссылкам
        netloc, path = urlsplit(script.attrs.get("src"))[1:3]
        if not netloc and path[-3:]==".js":
            script_url = urljoin(site_url, path)
            script_files.append(script_url)
    return script_files

def get_css_files(soup, site_url):
    css_files = []
    for css in soup.find_all("link"):
        if css.attrs.get("href"):
            netloc, path = urlsplit(css.attrs.get("href"))[1:3]
            # Качаем только по относительным ссылкам
            if not netloc and path[-4:]==".css":
                css_url = urljoin(site_url, path)
                css_files.append(css_url)
    return css_files

def get_media_files(soup, site_url):
    media_files = []
    for media in soup.find_all(["img","video","audio"]):
        # Качаем только по относительным ссылкам
        netloc, path = urlsplit(media.attrs.get("src"))[1:3]
        if not netloc:
            media_url = urljoin(site_url, path)
            media_files.append(media_url)
    return media_files

def get_hypertext_references(root_url, soup):
    references = set()

    for link in soup.find_all("a"):
        # Выбираем только относительные ссылки
        if link.attrs.get("href"):
            netloc, path = urlsplit(link.attrs.get("href"))[1:3]
            if not netloc:
                link_url = urljoin(root_url, path)
                references.add(link_url)
    return references

def save_content_page(path, name,  soup):
    full_name = os.path.join(path, name)
    with open(full_name, "w") as f:
        print(soup.prettify(), file=f)

def get_page_name(url):
    '''
    В Url может быть
    - только домен (https://example.com)
    - домен + path (https://example.com/path1/)
    - домен + path + имя файла (https://example.com/path1/index.html) 
    Функция вычленяет имя файла в последнем примере.
    Генерирует index.html для первого и второго примера
    '''
    path = urlsplit(url)[2]
    if not path:
        return "index.html"
    if path.endswith("/"):
        return "index.html"

    return os.path.basename(path)

def get_path_name(url):
    '''
    В Url может быть
    - только домен (https://example.com)
    - домен + path (https://example.com/path1/)
    - домен + path + имя файла (https://example.com/path1/index.html) 
    Функция возвращает имя домена в первом случае.
    И последний элемент пути без файла во втором и третьем случае
    '''
    netloc, path = urlsplit(url)[1:3]
    if not path:
        return netloc
    if path.endswith("/"):
        return path.split("/")[-2]
    return path.split("/")[-2]

def get_root_name(url):
    netloc, path = urlsplit(url)[1:3]
    if not path:
        return netloc
    raw_path = netloc, *path.split("/")[1:-1]
    return "/".join(raw_path)

def copy_pages_site(session, root_url, cur_url, root_dir, cur_level):
    if cur_level == 0:
        return "OK"
    content = get_page_content(session, cur_url)
    soup = BeautifulSoup(content,"lxml")
    save_content_page(root_dir, get_page_name(cur_url), soup)
    references = get_hypertext_references(cur_url, soup)
    for item_ref in references:
        if root_url == get_root_name(item_ref):
            # Если ссылка в текущей директории, сохраняем в нее очередной документ
            content = get_page_content(session, item_ref)
            soup = BeautifulSoup(content,"lxml")
            save_content_page(root_dir, get_page_name(item_ref), soup)
            for css_url in get_css_files(soup, item_ref):
                downloads_files(session, css_url, root_dir)
            for script_url in get_script_files(soup, item_ref):
                downloads_files(session, script_url, root_dir)
            for media_url in get_media_files(soup, item_ref):
                downloads_files(session, media_url, root_dir)
            continue
        #Ссылка отсылает на новый уровень, подготавливаем директории и корневые ссылки.
        #Проваливаемся по новому пути.
        new_root_dir = os.path.join(root_dir, get_path_name(item_ref))
        if not os.path.isdir(new_root_dir):
            os.mkdir(new_root_dir)
        new_root_url = get_root_name(item_ref)
        copy_pages_site(session, new_root_url, item_ref, new_root_dir, cur_level-1)

def downloads_files(session, url, root_dir):
    file_name = get_page_name(url)
    dir_name = get_path_name(url)
    full_path = os.path.join(root_dir, dir_name)
    if not os.path.isdir(full_path):
        os.mkdir(full_path)  
    full_path_name = os.path.join(root_dir, dir_name, file_name)
    response = session.get(url)
    with open(full_path_name, "wb") as file:
        file.write(response.content)

def main(site_url, site_dir, path_level):
    session = Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0"
    root_dir  = get_root_name(site_url).replace("/", "_")
    root_dir = os.path.join(site_dir, root_dir)
    if not os.path.isdir(root_dir):
        os.mkdir(root_dir)
    root_url = get_root_name(site_url)
    copy_pages_site(session, root_url, site_url, root_dir, path_level)
    
    file_paths = []
    for root, directories, files in os.walk(root_dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath) 

    full_name = os.path.join(site_dir, current_thread().name) + ".zip"
    with ZipFile(full_name,'w', ZIP_DEFLATED) as zip:
        for file in file_paths:
            zip.write(file) 
    
    rmtree(root_dir)



if __name__ == "__main__":
    main("https://docs.python.org", "sites", 2)