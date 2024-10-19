import os
import re
import requests
from bs4 import BeautifulSoup
import fitz
from zipfile import ZipFile
import glob

url_base = "https://overwatch.blizzard.com/en-us"
url_suffix = "/media/stories/"
output_dir = "output"

def main():
    index = requests.get(f"{url_base}{url_suffix}")
    soup = BeautifulSoup(index.text, "html.parser")
    # Completely optional list reversal because the books are listed in reverse chronological order
    links = soup.find_all('a', attrs={"data-type": "pdf"})[::-1] 

    for counter, link in enumerate(links):
        # Get the comic name from the page itself, also remove colons from names because Venture's comic throws an error on write
        name = re.sub(r'[:]', '', f"{link.find_all('h1')[0].text}") 
        page = f"{url_base}{link.get('href')}" 
        # Identify if it's a Comic or a Short Story
        doc_type = link['data-analytics'].split('-')[1].lstrip() 
        # Yes, Short Stories will be misspelled
        file_location = f"{output_dir}/Overwatch - {doc_type}s" 
        pdf_uri = f"{file_location}/{name}.pdf" 
        zip_uri = f"{file_location}/{name}.zip"

        book_metadata = {
            'name': name,
            'doc_type': doc_type,
            'download_link': get_download_link(page) # Get the actual download link
        }

        try:
            os.makedirs(file_location)
        except FileExistsError:
            print(f"Directory \"{file_location}\" already exists, continuing...")

        print(f"Attempting download: {book_metadata}...")
        book = requests.get(book_metadata['download_link'])
        print(f"Downloaded {book_metadata['name']}. Writing...")
        open(f"{pdf_uri}", 'wb').write(book.content)
        print(f"Wrote {book_metadata['name']} to disk at {pdf_uri}. Splitting...")

        with fitz.open(f"{pdf_uri}") as doc:
            for number, page in enumerate(doc.pages()):
                pix = page.get_pixmap()
                page_filename = f"{output_dir}/image_{str(number + 1)}.png"
                pix.save(page_filename)
            
        print(f"Split of {book_metadata['name']} complete! Zipping...")
        image_files = glob.glob(f"{output_dir}/*.png")

        with ZipFile(f"{zip_uri}", 'w') as myzip:
            for i, file in enumerate(image_files):
                # Have to use arcname to prevent images for being in an output folder inside the archive
                myzip.write(file, arcname=file.split('/')[1]) 
                os.remove(file)
        
        print(f"Zip Archive of {book_metadata['name']} complete! Cleaning up...")

        os.remove(pdf_uri)

        print(f"Processing of {book_metadata['name']} complete!")


def get_download_link(url):
    try:
        index = requests.get(f"{url}")
        soup = BeautifulSoup(index.text, "html.parser")
        return soup.find_all('a', class_="MediaSection-link MediaSection-link--download")[0].get('href')
    except IndexError:
        print(f"{url} not found")

if __name__ == "__main__":
    main()