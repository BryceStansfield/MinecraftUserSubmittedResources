from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
import pickle
from os import path
import os
import shutil
import datetime
import hashlib
from zipfile import ZipFile
import zipfile

bp = Blueprint('submit', __name__)

allowed_list = ["iron_boots", "iron_chestplate", "iron_leggings", "iron_helmet"]
item_to_layer = {
    "iron_boots": "iron_layer_1",
    "iron_chestplate": "iron_layer_1",
    "iron_leggings": "iron_layer_2", 
    "iron_helmet": "iron_layer_1"
}

@bp.route("/submit", methods=('GET', 'POST'))
def submit():
    if request.method == 'GET':
        return render_template("submit_new.jinja", items=allowed_list)
    else:
        form = request.form

        if check_name(form['Name'], form["EquipmentPiece"]):
            return "Name already being used for another texture"
        
        if form['password'] != current_app.config['SUBMISSION_PASSWORD']:
            return "Wrong password"

        add_textures_to_pack(form, request.files)
        zip_and_move()
        return "Texture uploaded successfully! Restart minecraft to test"

# Name dictionary functions
def load_name_dict():
    instance_path = current_app.instance_path
    pickle_path = path.join(instance_path, "used_names.pickle")

    if not path.exists(pickle_path):
        names_used = dict()
    else:
        with open(pickle_path, 'rb') as handle:
            names_used = pickle.load(handle)
    
    for item in allowed_list:
        if item not in names_used:
            names_used[item] = dict()
    
    return names_used

def append_name(name, item):
    existing = load_name_dict()
    existing[item][name]=True

    instance_path = current_app.instance_path
    pickle_path = path.join(instance_path, "used_names.pickle")
    
    with open(pickle_path, 'wb') as handle:
        pickle.dump(existing, handle)

def check_name(name, item):
    return name in load_name_dict()[item]

# Pre-existing hashes functions
def load_hashes_dict():
    instance_path = current_app.instance_path
    pickle_path = path.join(instance_path, "existing_hashes.pickle")

    if not path.exists(pickle_path):
        hashes_used = dict()
    else:
        with open(pickle_path, 'rb') as handle:
            hashes_used = pickle.load(handle)
    
    return hashes_used

def append_hash_dict(hash, file_name):
    existing = load_hashes_dict()
    existing[hash] = file_name

    instance_path = current_app.instance_path
    pickle_path = path.join(instance_path, "existing_hashes.pickle")
    
    with open(pickle_path, 'wb') as handle:
        pickle.dump(existing, handle)

def get_hash(file_loc):
    with open(file_loc, 'rb') as f:
        # BUF_SIZE is totally arbitrary, change for your app!
        BUF_SIZE = 65536  # lets read stuff in 64kb chunks!

        sha1 = hashlib.sha1()
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

def check_if_armor_exists(temp_file_loc):
    h = get_hash(temp_file_loc)
    existing_hashes = load_hashes_dict()

    if h in existing_hashes:
        return (True, existing_hashes[h],)
    else:
        return (False, "",)


# File moving functions
def prepare_temp(instance_path):
    # Making sure temp_dir exists and is empty
    temp_dir = path.join(instance_path, "temp")
    if path.exists(temp_dir):
        if path.isfile(temp_dir):
            os.remove(temp_dir)
        else:
            shutil.rmtree(temp_dir)

    os.mkdir(temp_dir)

    return temp_dir

def ensure_pack_initialized(pack_path):
    armor_path = path.join(pack_path, "assets", "minecraft", "optifine", "cit", "armor")
    items_path = path.join(pack_path, "assets", "minecraft", "optifine", "cit", "items")
    if not path.exists(armor_path):
        os.makedirs(armor_path)

    if not path.exists(items_path):
        os.makedirs(items_path)

def add_textures_to_pack(form, files):
    # Getting the packs path and setting folders up
    instance_path = current_app.instance_path
    temp_path = prepare_temp(instance_path)
    pack_path = path.join(instance_path, "pack")
    ensure_pack_initialized(pack_path)

    # Let's add these files to temp/ with a funny name
    time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    armor_name = time_str+"armor.png"
    armor_path = path.join(temp_path, armor_name)
    item_name = time_str+"item.png"
    item_path = path.join(temp_path, item_name)
    files['armorTexture'].save(armor_path)
    files['itemTexture'].save(item_path)

    # Now let's check if this armor already exists
    armor_exists = check_if_armor_exists(armor_path)
    if armor_exists[0]:
        armor_name = armor_exists[1]

    ### Adding to the pack
    optifine_path = path.join(pack_path, "assets", "minecraft", "optifine", "cit")

    # Let's add the item
    optifine_item_path = path.join(optifine_path, "items", item_name)
    optifine_item_properties_path = path.join(optifine_path, "items", time_str + "item.properties")
    shutil.copyfile(item_path, optifine_item_path)

    with open(optifine_item_properties_path, 'w') as f:
        f.write("type=item\n")
        f.write(f"items={form['EquipmentPiece']}\n")
        f.write(f"texture={item_name}\n")
        f.write(f"nbt.display.Name={form['Name']}\n")


    # And let's (maybe) add the armor
    optifine_armor_path = path.join(optifine_path, "armor", armor_name)
    optifine_armor_properties_path = path.join(optifine_path, "armor", time_str + "armor.properties")

    if not armor_exists[0]:
        shutil.copyfile(armor_path, optifine_armor_path)
    
    with open(optifine_armor_properties_path, 'w') as f:
        f.write("type=armor\n")
        f.write(f"items={form['EquipmentPiece']}\n")
        f.write(f"texture.{item_to_layer[form['EquipmentPiece']]}={armor_name}\n") #TODO: Add mapping
        f.write(f"nbt.display.Name={form['Name']}\n")

    # Finally, let's add the hashes and names to our dicts:
    if not armor_exists[0]:
        h = get_hash(armor_path)
        append_hash_dict(h, armor_name)
    append_name(form['Name'], form['EquipmentPiece'])
    return

# Zipping + moving functions
def zipdir(parent_dir : str , ziph : ZipFile, prefix="") -> None:
    for thing in os.listdir(parent_dir):
        ziph.write(path.join(parent_dir, thing), prefix+thing)
        if path.isdir(path.join(parent_dir, thing)):
            zipdir(path.join(parent_dir, thing), ziph, prefix=prefix+f"{thing}/")


def zip_and_move():
    # Getting the packs path
    instance_path = current_app.instance_path
    pack_path = path.join(instance_path, "pack")

    # Delete our zip if it already exists
    zip_path = path.join(instance_path, current_app.config['RESOURCE_PACK_NAME']+".zip")
    if path.exists(zip_path):
        os.remove(zip_path)

    # zip pack_path into zip_path
    zip = zipfile.ZipFile(zip_path, 'w')
    zipdir(pack_path, zip)
    zip.close()
    h = get_hash(zip_path)

    # And moving the pack to the appropriate location
    move_resource_pack(zip_path, current_app.config['RESOURCE_PACK_DIR'], current_app.config['RESOURCE_PACK_NAME']+".zip")

    # Finally, setting up the properties
    redo_properties(current_app.config['SERVER_PROPERTIES_LOCATION'],
                    current_app.config['WEB_ADDRESS'],
                    current_app.config['RESOURCE_PACK_NAME']+".zip",
                    h)

def move_resource_pack(new_pack_path, resource_pack_directory, resource_pack_name):
    # Moving the existing resource pack
    www_path = os.path.join(resource_pack_directory, resource_pack_name)
    print(www_path)
    if os.path.exists(www_path):
        backup_dir = os.path.join(resource_pack_directory, "backups")
        if not os.path.exists(backup_dir):
            os.mkdir(backup_dir)

        os.replace(www_path, os.path.join(resource_pack_directory, "backups", resource_pack_name+datetime.datetime.now().strftime("%Y%m%d%H%M%S")+".zip"))

    # Popping the new one in
    shutil.copyfile(new_pack_path, www_path)

# Properties altering functions
def redo_properties(prop_loc, www_dir, resource_pack_name, sha_digest):
    # Copying the old properties (with some modifications)
    f_old = open(prop_loc, 'r')
    f_new = open(prop_loc+"temp", 'w')

    lines = f_old.readlines()
    for line in lines:
        if line.startswith("resource-pack-sha1="):
            f_new.write("resource-pack-sha1=" + sha_digest + '\n')
        elif line.startswith("resource-pack="):
            f_new.write("resource-pack=" + www_dir + resource_pack_name + "?dl=1" + '\n')
        else:
            f_new.write(line)
    f_old.close()
    f_new.close()

    # Replacing the old properties
    os.replace(prop_loc+"temp", prop_loc)
    f_old.close()