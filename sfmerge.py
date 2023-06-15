# Merge this file into sharedfunctions.py

import os, shutil

import zipfile
import tempfile
import re

# libs for encrypting APIKeys
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

csitools_dir='/opt/csitools/'

#------------------------- APIKeys encryption methods --------------------------------------------#

def genKey(password=0):     # generate key for Fernet() using password.
    # genKey doesn't stores key for a better security, generates it at runtime.   
    if password == 0:
        password = input("Enter Password: ").encode()
    else:
        password = password.encode()
    salt=b"Just4FillingTheRequirementOfPBKDF2HMAC"  
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000
    )
    derived=kdf.derive(password)
    key = base64.urlsafe_b64encode(derived)
    return key
    
def encrypt(key):
    f = Fernet(key)

    # encrypting APIKeys.json
    with open(f'{csitools_dir}APIKeys.json', 'rb') as plain_file:
        plain_data = plain_file.read()
    
    encrypted_data = f.encrypt(plain_data)

    with open(f'{csitools_dir}APIKeys.enc', 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)

    # Removing plaintext data file
    os.remove(f'{csitools_dir}APIKeys.json')
    
    return True

def decrypt(key):
    f = Fernet(key)

    try:
        # Decrypting APIKeys.enc
        with open(f'{csitools_dir}APIKeys.enc', 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()
        
        plain_data = f.decrypt(encrypted_data)

        with open(f'{csitools_dir}APIKeys.json', 'wb') as plain_file:
            plain_file.write(plain_data)
    
        return True
    
    except InvalidToken:
        print("Invalid Password to Decrypt")
        return False


def reportme(tmpl_path,out_path,data_dict, img_dict=None):
    """
    fill_template(tmpl_path, out_path, data_dict, img_list):
        Fills in the fields of the template document with data and generates a result document.

    Args:
        tmpl_path (str): Path of the template document that contains the fields to be filled in.
        out_path (str): Path of the resulting document with placeholders replaced by data.
        data_dict (dict): A dictionary mapping placeholder names to their corresponding values for replacement.
        img_list (dict): A dictionary specifying the images to replace in the document. 
            Key: The position of the image, docx and odt have different positions arrangement.
            Value: The path to the image file.

    Note:
    - In ODT files: Position of Images depends on the order of adding them not the format of document.
        - if someone adds the image first but adds it to the last page still it will gonna have 0 position.
    - In DOCX files: Position of Images depends on the format of document.
        - if someone adds the image first but adds it to the last page then it will gonna have last position.

    Example:
        tmpl_path = 'template.odt'
        out_path = 'result.odt'
        data_dict = {'placeholder1': 'value1', 'placeholder2': 'value2'}
        img_list = {0: 'image1.png', 1: 'image2.png'}
        fill_template(tmpl_path, out_path, data_dict, img_list)
    """
    
    if tmpl_path.lower().endswith(".odt"):
       
        # Create a temporary directory to extract the ODT contents
        temp_dir = tempfile.mkdtemp()

        # Extract the ODT contents to the temporary directory
        with zipfile.ZipFile(tmpl_path, 'r') as odt_file:
            odt_file.extractall(temp_dir)

        # Read the styles.xml file for header and footer
        content_path = os.path.join(temp_dir, 'styles.xml')
        with open(content_path, 'r') as content_file:
            content = content_file.read()
            content_file.close()
        
        # regex pattern to find placeholder and replace with the value
        for placeholder, value in data_dict.items(): 
            content = re.sub(rf'<text:user-defined[^&]*?>&lt;{placeholder}&gt;</text:user-defined>', value, content)

        # Write the modified content back to styles.xml
        with open(content_path, 'w') as modified_file:
            modified_file.write(content)
            modified_file.close()

        # Read the content.xml file
        content_path = os.path.join(temp_dir, 'content.xml')
        with open(content_path, 'r', encoding='utf-8') as content_file:
            content = content_file.read()
            content_file.close()

        # regex pattern to find placeholder and replace with the value
        for placeholder, value in data_dict.items():
            # dealing with adding multi line value to the variable in xml using heavy regex
            if '\n' in value:
                values = value.split('\n')

                main_search_string = f'<text:user-defined[^&]*?>&lt;{placeholder}&gt;</text:user-defined>'

                occurrences = re.finditer(rf'({main_search_string})(.*?</text:p>)', content)

                for count, occurrence in enumerate(occurrences):
                    temp = re.search(rf'<.*>', occurrence.group(2))
                    posttext = temp.group()
                    tags = posttext.strip('</>')
                    tags = tags.split('></')
                    
                    re_pretext = ''
                    for i in range(0, len(tags)):
                        tag = tags[len(tags) - i - 1]
                        re_pretext += f'(<{tag}[^>]*>)'
                        if tag == 'text:p':
                            re_pretext += '(?:(?!<text:p).)*?'

                    temp = re.search(rf'{re_pretext}({main_search_string})(.*?</text:p>)', content)

                    pretext = ''
                    for i in range(0, len(tags)):
                        pretext += temp.group(i + 1)

                    data_multiline = ''
                    for i, val in enumerate(values):
                        if i == 0:
                            data_multiline += f"{val}{posttext}"
                        elif i == len(values) - 1:
                            data_multiline += f'{pretext}{val}'
                        else:
                            data_multiline += f'{pretext}{val}{posttext}'
                    content = re.sub(re.escape(occurrence.group(1)), data_multiline, content, count=count+1)

            else:
                content = re.sub(rf'<text:user-defined[^&]*?>&lt;{placeholder}&gt;</text:user-defined>', value, content)

        # replace the placeholder images
        if not img_dict == None:
            file_names = re.findall(r'"Pictures/([^"]+)"', content)
            try:
                for num, imgPath in img_dict.items():
                    shutil.copy(imgPath,os.path.join(temp_dir, f'Pictures/{file_names[len(file_names)-int(num)-1]}'))
            except IndexError:
                print(f'You have only {len(file_names)} image/s in the doc. Index starts from 0')
                
        # Write the modified content back to content.xml
        with open(content_path, 'w') as modified_file:
            modified_file.write(content)
            modified_file.close()
        # Create a new ODT file with the modified content
        with zipfile.ZipFile(out_path, 'w') as modified_odt:
            # Add the modified content.xml back to the ODT
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    modified_odt.write(file_path, arcname)

        # print("Modified file saved as:", out_path)
        # print(temp_dir)
        shutil.rmtree(temp_dir)
    
    if tmpl_path.lower().endswith(".docx"):
        # Create a temporary directory to extract the DOCX contents
        temp_dir = tempfile.mkdtemp()

        # Extract the ODT contents to the temporary directory
        with zipfile.ZipFile(tmpl_path, 'r') as odt_file:
            odt_file.extractall(temp_dir)
        
        content_path = os.path.join(temp_dir, 'word','header1.xml')
        # Read the header.xml and footer.xml file for header and footer
        if  os.path.isfile(content_path):
            # header.xml
            with open(content_path, 'r') as content_file:
                content = content_file.read()
                content_file.close()
            
            # regex pattern to find placeholder and replace with the value
            for placeholder, value in data_dict.items(): 
                content = re.sub(rf'&lt;{placeholder}&gt;', value, content)

            # Write the modified content back to styles.xml
            with open(content_path, 'w') as modified_file:
                modified_file.write(content)
                modified_file.close()

            # footer.xml
            content_path = os.path.join(temp_dir, 'word','footer1.xml')
            with open(content_path, 'r') as content_file:
                content = content_file.read()
                content_file.close()
            
            # regex pattern to find placeholder and replace with the value
            for placeholder, value in data_dict.items(): 
                content = re.sub(rf'&lt;{placeholder}&gt;', value, content)

            # Write the modified content back to styles.xml
            with open(content_path, 'w') as modified_file:
                modified_file.write(content)
                modified_file.close()
        
        # Read the document.xml file
        content_path = os.path.join(temp_dir, 'word', 'document.xml')
        with open(content_path, 'r', encoding='utf-8') as content_file:
            content = content_file.read()
            content_file.close()
        
        # regex pattern to find placeholder and replace with the value
        for placeholder, value in data_dict.items():
            # dealing with adding multi line value to the variable in xml using heavy regex
            # if False:
            if '\n' in value:
                values = value.split('\n')

                main_search_string = f'&lt;{placeholder}&gt;'
                
                occurrences = re.finditer(rf'(<w:p>(?:(?!<w:p>).)*?)(<w:r>(?:(?!<w:r>).)*?)<w:t>[^<>]*?({main_search_string})', content)
                

                for count, occurrence in enumerate(occurrences):    
                    # pretext to add new line
                    # condition to check if placeholder is in bullet point then add new <w:p>
                    if '<w:numPr><w:ilvl w:val="0"/>' in occurrence.group(1):   
                        # This is just like pressing enter in docx
                        # print('list found!')
                        pretext = occurrence.group(1) + occurrence.group(2) + '<w:t>'
                        posttext = '</w:t></w:r></w:p>'
                    # if not bullet point then to keep the consistent style just do <w:br>
                    else:
                        # This is just like pressing shift + enter in docx
                        pretext = occurrence.group(2) + '<w:br w:type="textWrapping"/></w:r>' + occurrence.group(2) + '<w:t>'
                        posttext = '</w:t></w:r>'
                        

                    data_multiline = ''
                    for i, val in enumerate(values):
                        if i == 0:
                            data_multiline += f"{val}{posttext}"
                        elif i == len(values) - 1:
                            data_multiline += f'{pretext}{val}'
                        else:
                            data_multiline += f'{pretext}{val}{posttext}'

                    content = re.sub(re.escape(occurrence.group(3)), data_multiline, content, count=count+1)

            else:
                content = re.sub(rf'&lt;{placeholder}&gt;', value, content)

        # replace the placeholder images
        if not img_dict == None:
            img_dir = os.path.join(temp_dir,'word','media')
            file_names = os.listdir(img_dir)
            try:
                for num, imgPath in img_dict.items():
                    shutil.copy(imgPath,os.path.join(img_dir, f'{file_names[int(num)]}'))
                    print
            except IndexError:
                print(f'You have only {len(file_names)} image/s in the doc. Index starts from 0')
                
        # Write the modified content back to content.xml
        with open(content_path, 'w') as modified_file:
            modified_file.write(content)
            modified_file.close()
        # Create a new ODT file with the modified content
        with zipfile.ZipFile(out_path, 'w') as modified_odt:
            # Add the modified content.xml back to the ODT
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    modified_odt.write(file_path, arcname)

        # print("Modified file saved as:", out_path)
        # print(temp_dir)
        shutil.rmtree(temp_dir)
