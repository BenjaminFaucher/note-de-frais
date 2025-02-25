#!/usr/bin/env python
# coding: utf-8



from flask import Flask, render_template, request, send_file
from pdfrw import PdfReader, PdfWriter, PageMerge
import os
import fitz
import numpy as np
from PyPDF2 import PdfMerger
from datetime import date
from werkzeug.utils import secure_filename

ajd = date.today()
ajd = str(ajd)[8:] + "/" + str(ajd)[5:7] + "/" + str(ajd)[:4]

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Chemins des fichiers PDF d'origine
NOTE_DE_FRAIS_TEMPLATE = 'note_de_frais.pdf'
ORDRE_DE_MISSION_TEMPLATE = 'ordre_de_mission.pdf'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Route pour afficher le formulaire
@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        # Récupération des données du formulaire
        nom = request.form["nom"]
        fonction = request.form["fonction"]
        mission = request.form['mission']
        date_debut = request.form['date_debut']
        date_fin = request.form['date_fin']
        lieu = request.form['lieu']
        n = int(request.form['n'])
        n2 = int(request.form['n2'])

        # Récupération des informations de chaque personne
        personnes = []
        justificatifs = []
        files_justificatifs = []
        

        if n > 8:
            personnes_file = request.files.get('personnes_fichier')
            files_justificatifs.append(personnes_file)
        else:
            for i in range(n):
                prenomi = request.form[f'prenom_{i}']
                nomi = request.form[f'nom_{i}']
                fonctioni = request.form[f'fonction_{i}']
                delegationi = request.form[f'delegation_{i}']
                personnes.append({'prenom': prenomi, 'nom': nomi, 'fonction': fonctioni, 'delegation': delegationi})

            
        for i in range(n2):
            nature = request.form[f'nature_{i}']
            montant = request.form[f'montant_{i}']
            justificatifs.append({'Nature': nature , 'Montant' : montant})
            fichier = request.files[f'fichier_{i}']
            files_justificatifs.append(fichier)
        
        
            
            

        rib_deja_donne = 'rib_deja_donne' in request.form

        if rib_deja_donne:
            rib_status = "RIB déjà donné"
            rib_fichier = None
        else:
            # Gestion du fichier RIB téléchargé
            rib_file = request.files.get('rib_fichier')
            files_justificatifs.append(rib_file)

        # Génération des PDFs remplis
        ordre_de_mission = fill_pdf_ordre_de_mission(mission, date_debut, date_fin, lieu, "Adrien Dumont Passegio", justificatifs, personnes)
        note_de_frais = fill_pdf_note_de_frais(nom,fonction,date_debut,ajd,mission,justificatifs)
        pdf_final = create_pdf_final(note_de_frais,ordre_de_mission,files_justificatifs)
        
        
        # Retourne les fichiers PDF générés pour téléchargement
        return send_file(pdf_final, as_attachment=True)

    return render_template('form.html')


def formatdate(date,t):
    date = str(date)
    if t == 1:
        return date[8:10] + "/" + date[5:7] + "/" + date[:4]
    if t == 2:
        return date[8:10] + "/" + date[5:7] + "/" + date[:4] + " " + date[11:13] + "h" + date[14:]


def fill_pdf_ordre_de_mission(mission, date_debut, date_fin, lieu, responsable, justificatifs, personnes):
    pdf_path = 'ordre_de_mission.pdf'
    doc = fitz.open(pdf_path)

    page = doc[0]

    budget = np.sum([float(justificatifs[i]["Montant"]) for i in range(len(justificatifs))])
    
    page.insert_text((215, 160), "Unité locale Paris XII", fontsize=12)
    page.insert_text((215, 180), "14 Bd Soult, 75012", fontsize=12)
    
    
    page.insert_text((215, 230), f'{mission}', fontsize=12)
    page.insert_text((215, 250), f'{date_debut}', fontsize=12)
    page.insert_text((215, 269), f'{date_fin}', fontsize=12)
    page.insert_text((215, 289), f'{lieu}', fontsize=12)
    page.insert_text((215, 308), f'{responsable}', fontsize=12)

    page.insert_text((200, 610), "remboursement des frais", fontsize=12)
    page.insert_text((200, 640), f'{budget}', fontsize=12)
    
    


    for idx, p in enumerate(personnes):
            page.insert_text((75, 385 + idx*21), f'{p["nom"]}', fontsize=12)
            page.insert_text((186, 385 + idx*21), f'{p["fonction"]}', fontsize=12)
            page.insert_text((286, 385 + idx*21), f'{p["delegation"]}', fontsize=12)


    output_path = 'ordre_de_mission_rempli.pdf'
    doc.save(output_path)
    doc.close()

    return output_path





def fill_pdf_note_de_frais(nom,fonction,date_mission,date,objet,justificatifs):

    pdf_path = 'note_de_frais.pdf'
    doc = fitz.open(pdf_path)

    date_mission = formatdate(date_mission,2)


    somme = np.sum([int(justificatifs[i]["Montant"]) for i in range(len(justificatifs))])

    page = doc[0]
    page.insert_text((150, 130), f'{nom}', fontsize=12)
    page.insert_text((150, 150), f'{fonction}', fontsize=12)
    page.insert_text((450, 140), f'{date}', fontsize=12)
    page.insert_text((362,516),f'{somme}' + " euros")




    for idx, p in enumerate(justificatifs):
        if idx < 10:
            page.insert_text((75, 225 + idx*20), f'{idx}', fontsize=12)
            page.insert_text((105, 225 + idx*20), f'{date_mission} {objet}', fontsize=10)
            page.insert_text((250, 225 + idx*20), f'{p["Nature"]}', fontsize=12)
            page.insert_text((362, 225 + idx*20), f'{str(p["Montant"]) + " euros"}', fontsize=12)
        else:
            page.insert_text((75, 240 + idx*18), f'{idx}', fontsize=12)
            page.insert_text((105, 240 + idx*18), f'{date_mission} {objet}', fontsize=10)
            page.insert_text((250, 240 + idx*18), f'{p["Nature"]}', fontsize=12)
            page.insert_text((362, 240 + idx*18), f'{str(p["Montant"]) + " euros"}', fontsize=12)

        

    page.insert_text((68, 592), "X", fontsize=20)
    

    output_path = 'note_de_frais_rempli.pdf'
    doc.save(output_path)
    doc.close()
    return(output_path)




def create_pdf_final(note_de_frais,ordre_de_mission,files_justificatifs):

    merger = PdfMerger()
    merger.append(note_de_frais)
    merger.append(ordre_de_mission)

    for i in range(len(files_justificatifs)):
        merger.append(files_justificatifs[i])


    output_path = 'note_de_frais_rempli.pdf'
    merger.write(output_path)
    merger.close()
    return(output_path)

if __name__ == "__main__":
    #app.run(host="0.0.0.0", port=5000, debug=True)
    app.run(host="0.0.0.0", port=5001, debug=False)
#if __name__ == "__main__":
    #app.run(debug=True)





