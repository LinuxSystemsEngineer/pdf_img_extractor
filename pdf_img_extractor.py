#!/usr/bin/env python3 

import os
import hashlib
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
from multiprocessing import Pool, cpu_count

# Configuration
IMG_DIR = './img'
PDF_DIR = './pdf'
HASH_SET = set()  # Set to store unique image hashes

# Ensure necessary directories are present
def setup_directories():
    if os.path.exists(IMG_DIR):
        for filename in os.listdir(IMG_DIR):
            file_path = os.path.join(IMG_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print(f"Cleared existing images from '{IMG_DIR}' folder.")
    else:
        os.makedirs(IMG_DIR)

# Calculate the SHA-256 hash of an image
def calculate_image_hash(image_bytes):
    hasher = hashlib.sha256()
    hasher.update(image_bytes)
    return hasher.hexdigest()

# Save an image if it's unique
def save_image(image_bytes, page_num, img_index):
    try:
        # Calculate hash and check for duplicates
        image_hash = calculate_image_hash(image_bytes)
        
        if image_hash in HASH_SET:
            print(f"[STATUS] Skipped dupe image on page {page_num + 1}, image {img_index + 1}")
            return False  # Duplicate image, do not save
        else:
            # Mark this image as processed
            HASH_SET.add(image_hash)

            # Convert bytes to PIL image and save
            pil_image = Image.open(BytesIO(image_bytes))
            image_filename = f"{IMG_DIR}/image_{page_num + 1}_{img_index + 1}.png"
            pil_image.save(image_filename)
            print(f"[STATUS] Saved OG image {image_filename}")
            return True  # Unique image, saved successfully
    except Exception as e:
        print(f"[ERROR] Error saving image on page {page_num + 1}, image {img_index + 1}: {e}")
        return False

# Extract images from a single page
def extract_images_from_page(args):
    pdf_file_path, page_num = args
    try:
        # Open the document within the worker process
        pdf_document = fitz.open(pdf_file_path)
        page = pdf_document.load_page(page_num)
        image_list = page.get_images(full=True)
        images_extracted = 0

        # Extract each image
        for img_index, img in enumerate(image_list):
            xref = img[0]  # The image reference

            # Get the image data
            image = pdf_document.extract_image(xref)
            image_bytes = image["image"]

            # Save the image if it's unique
            if save_image(image_bytes, page_num, img_index):
                images_extracted += 1
        
        return images_extracted
    except Exception as e:
        print(f"[ERROR] Error processing page {page_num + 1}: {e}")
        return 0

# Master function to manage multiprocessing
def extract_images_from_pdf(pdf_file_path):
    # Prepare directories
    setup_directories()

    # Get the total number of pages
    pdf_document = fitz.open(pdf_file_path)
    total_pages = pdf_document.page_count
    pdf_document.close()

    # Create a list of page numbers to process
    tasks = [(pdf_file_path, page_num) for page_num in range(total_pages)]

    # Use all available CPU cores
    num_workers = cpu_count()
    print(f"[STATUS] Using {num_workers} workers...")

    # Use multiprocessing Pool for concurrent processing
    with Pool(processes=num_workers) as pool:
        results = pool.map(extract_images_from_page, tasks)
    
    total_images_extracted = sum(results)
    if total_images_extracted == 0:
        print("[STATUS] No OG images found in the PDF.")
    else:
        print(f"[STATUS] Total {total_images_extracted} OG images saved!")

# List all .pdf files in the ./pdf folder
def list_pdf_files():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
    return pdf_files

# Main program logic
if __name__ == "__main__":
    print("Welcome to the PDF Image Extractor Program!")
    print("This program will extract all unique images from a PDF stored inside the './pdf' folder and save them into the './img' folder in the current directory.")
    print("Please make sure the PDF you want to extract images from is located in the './pdf' folder.")

    # List all available PDF files in the ./pdf folder
    pdf_files = list_pdf_files()

    if not pdf_files:
        print("No PDF files found in the './pdf' folder. Please make sure to place your PDF files in the './pdf' folder.")
    else:
        # Display the list of PDFs to the user
        print("\nAvailable PDF files in './pdf' folder:")
        for idx, pdf in enumerate(pdf_files, 1):
            print(f"{idx}. {pdf}")

        # Prompt the user to choose a PDF file by number
        try:
            pdf_choice = int(input("\nEnter the number of the PDF file you would like to extract images from: "))
            
            if pdf_choice < 1 or pdf_choice > len(pdf_files):
                print("Invalid selection. Please choose a valid number from the list.")
            else:
                # Get the selected PDF file
                selected_pdf = pdf_files[pdf_choice - 1]
                selected_pdf_path = f"{PDF_DIR}/{selected_pdf}"
                print(f"\nYou selected: {selected_pdf}")
                
                # Extract images from the chosen PDF file using multiprocessing
                extract_images_from_pdf(selected_pdf_path)
        except ValueError:
            print("Invalid input. Please enter a number corresponding to the PDF file.")

