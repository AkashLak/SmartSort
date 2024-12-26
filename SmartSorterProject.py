
import os
from shutil import move
from datetime import datetime
#PIL used to analyze images, and Exiftags is used to find the date of photo taken, along with what it was taken with and where it was taken
from PIL import Image, ExifTags
#hachoir parser used to allow the library to understand and analyze the file. Then extract metadata allows to get creation date, duration, file type, resolution from a file using a parser
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
import PyPDF2
from docx import Document

def photo_metadata(filepath):
    try:
        image = Image.open(filepath)
        exif_data = image._getexif()
        
        #return none if nothing in dictionary
        if not exif_data:
            print(f"No exif data found for {image}, using file creation date")
            #Getting creation time of file
            creation_time = os.path.getctime(filepath)
            #Create a datetime object, then converting into year month date format
            return datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d")
        #Loop through key value pairs, with the key being tag, and value being value. Change the exif_data to a list with the items method specifically made for dictionaries
        for tag, value in exif_data.items():
            #Decode the tag number to human readable text using the get method, and supplying (tag, tag), with the first tag being the actual number, and the second tag being a default value if no human text found
            decoded_tag = ExifTags.get(tag, tag)
            #Checking if the decoded text is datetimeoriginal, and if so we want the specific date of the image
            if decoded_tag == "DateTimeOriginal":
                #Splitting the value which has the date and etc, into a list. Then splitting based on a space found in the value, and only lookign at the first index which is the date portion. Then converting all colons with a - for proper format
                return value.split(" ")[0].replace(":","-")
    #Supplying Exception to catch all possible errors, and not a specific one. 
    except Exception:
        print(f"Error reading photo metadata {Exception}")
    return None      

def video_metadata(filepath):
    try:
        #Parsed representation of video file, in order to access hidden information
        parse_vid = createParser(filepath)
        #Extracting metadata of the video in the form of a dictionary (key:value)
        metadata_vid = extractMetadata(parse_vid)
        
        if not metadata_vid:
            return None
        else:
            #get method is used by supplying the key, and finding the value associated with it. The .strftime stands for string format time, where it puts the date in a strng format of year-month-day
            return metadata_vid.get("creation_date").strftime("%Y-%m-%d")
    except Exception:
        print(f"Error reading video metadata {Exception}")
    return None 

def pdf_metadata(filepath):
    try:
        #Opening in rb mode meaning read binary mode. Because not a regular text file and contains pdfs, images etc
        file = open(filepath, "rb")
        pdf_read = PyPDF2.PdfFileReader(file)
        pdf_metadata = pdf_read.getDocumentInfo()

        #Checking if creation date is in the metadata pdf key
        if "/CreationDate" in pdf_metadata:
            #Getting the specific value of the CreationDate key by passing the key as an index. 
            creation_date = pdf_metadata["/CreationDate"]
            #Checking if the value starts with D:, which it sometimes does
            if creation_date.startswith("D:"):
                #Then if it stats with D:, it would take the index 2:10, to only get the date value needed
                creation_date = creation_date[2:10]
            return creation_date
        else:
            print(f"No creation date found in PDF metadata: {filepath}")
            return None
    except Exception:
        print(f"Error reading pdf metadata {Exception}")
    return None 

def docx_metadata(filepath):
    try:
        #Creating an instance of the Document class and the object doc
        doc = Document(filepath)
        #Creating an object core_properties with the .core_properties attributes, which shows the core properties of the Word document
        core_properties = doc.core_properties
        #Getting the creation date from the core_propeties object by using the attribute .created
        creation_date = core_properties.created
        #Formatting the creation date to year month date
        return creation_date.strftime("%Y-%m-%d")
    except Exception:
        print(f"Error reading docx metadata {Exception}")
    return None 
    
def file_metadata(filepath):
    try:
        if filepath.lower().endswith(("jpg", "jpeg", "png", "gif")):
            creation_date = photo_metadata(filepath)
        elif filepath.lower().endswith(("mp4", "avi", "mov", "mkv")):
            creation_date = video_metadata(filepath)
        elif filepath.lower().endswith("pdf"):
            creation_date = pdf_metadata(filepath)
        elif filepath.lower().endswith("docx"):
            creation_date = docx_metadata(filepath)
        else:
            creation_date = None
        
        if creation_date:
            #Using splitext because its designed for splitting file names into 2 parts. the root is everything before the extension, and the extension is everyhting after the last dot
            #Then using index [1] in order to just get the extension name, and convert to lowercase
            file_extension = os.path.splitext(filepath)[1].lower()
            return creation_date, file_extension
        else:
            return None, None
    
    except Exception:
        print(f"Error extracting file metadata: {Exception}")
        return None, None

def organize_files(filepath, root_directory = "SmartSort"):
    try:
        creation_date, file_extension = file_metadata(filepath)

        if not creation_date:
            print(f"No valid metadata found for {filepath}")
            return None

        image_extensions = {".jpg", ".jpeg", ".png", ".gif"}
        video_extensions = {".mp4", ".avi", ".mov", ".mkv"}
        document_extensions = {".pdf", ".docx"}

        if file_extension in image_extensions:
            file_category = "Images"
        elif file_extension in video_extensions:
            file_category = "Videos"
        elif file_extension in document_extensions:
            file_category = "Documents"
        else:
            print(f"Unsupported file type: {filepath}")
            return None

        #lstrp means removing leftside period. Need to do this because fileysystems restrict file names with characters like a leadng .
        file_extension = file_extension.lstrip('.')

        #Joining file path names together. Basically concatenating the root directory name with the file category, file extension and the creation date all into 1 pathway
        organized_dir = os.path.join(root_directory, file_category, file_extension, creation_date)
        print(f"Organizing file into: {organized_dir}")
        #Making the organization directory and setting exist_ok to True as a default so no error will be raised if the target directory already exists
        os.makedirs(organized_dir, exist_ok = True)

        #Creating a new file path with the organization directory and joining it with the main base name portion of the full path. 
        #Example: /home/user/documents/example_file.txt and returns just example_file.txt, which is the last part of the path, i.e., the file name with its extension.
        new_file_path = os.path.join(organized_dir, os.path.basename(filepath))
        print(f"Moving file to: {new_file_path}")
        #Using the move function to move the file from the original file path to the new file path
        move(filepath,new_file_path)

        return f"File moved to {new_file_path}"
    
    except Exception:
        print(f"Error organizing file: {Exception}")
        return None

def main():
    
    #Initializing the source directory where I take the files from, and then the root directory, where I place the files
    source_directory = "/Users/akashlakshmanan/Downloads"
    root_directory = "/Users/akashlakshmanan/Desktop/SmartSort"

    #Looping through the downloads folder using os.listdir which lists all the files and directories in the folder, with the loop variable filename
    for filename in os.listdir(source_directory):
        #Joining the source directory file path with the filenames in the downloads directory to create the original filepath
        filepath = os.path.join(source_directory, filename)
        #Checking if the original filepath is actually a file and exists
        if os.path.isfile(filepath):
            result = organize_files(filepath, root_directory)
            if result:
                print(result)

if __name__ == "__main__":
    main()
