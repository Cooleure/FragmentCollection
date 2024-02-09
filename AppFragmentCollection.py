import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import cv2
from PIL import Image

class DetectChanges:
    def __init__(self, video_path, output_folder, change_threshold, app):
        self.video_path = video_path
        self.output_folder = output_folder
        self.change_threshold = change_threshold
        self.stop = False
        self.app = app

    def get_video_progress(self, current_frame, total_frames):
        return (current_frame / total_frames) * 100

    def detect_changes(self):
        # Lecture de la vidéo
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print("Erreur : Impossible d'ouvrir la vidéo.")
            return
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Création du dossier de sortie avec le nom du fichier vidéo
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        output_folder_video = os.path.join(self.output_folder, f"Output_{video_name}")
        os.makedirs(output_folder_video, exist_ok=True)

        # Initialisation de la frame précédente
        ret, previous_frame = cap.read()
        if not ret:
            print("Erreur : Impossible de lire la première frame de la vidéo.")
            cap.release()
            return

        # Initialisation de l'indice du dernier screenshot pris
        last_screenshot_index = 0

        while cap.isOpened() and not self.stop:
            # Lecture de la frame suivante
            ret, frame = cap.read()
            if not ret:
                break

            # Convertir les frames en niveaux de gris pour faciliter la comparaison
            previous_gray = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Calcul de la différence absolue entre les deux frames
            frame_diff = cv2.absdiff(previous_gray, gray)

            # Seuil pour déterminer les pixels qui représentent un changement significatif
            threshold = 30
            _, thresholded_diff = cv2.threshold(frame_diff, threshold, 255, cv2.THRESH_BINARY)

            # Calculer le pourcentage de pixels changés
            changed_pixels_percentage = (cv2.countNonZero(thresholded_diff) / (frame.shape[0] * frame.shape[1])) * 100

            # Si le pourcentage de pixels changés dépasse le seuil spécifié, on considère qu'il y a eu un changement de plan
            if changed_pixels_percentage > self.change_threshold:
                # Prendre un screenshot de la frame courante
                screenshot_index = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                if screenshot_index - last_screenshot_index > 10:  # Assurez-vous qu'il y ait une certaine distance entre les screenshots
                    screenshot_path = os.path.join(output_folder_video, f'{video_name}_{screenshot_index:04d}.jpg')
                    cv2.imwrite(screenshot_path, frame)
                    last_screenshot_index = screenshot_index
                    print(f"Screenshot pris à la frame {screenshot_index}.")
                    self.app.image_render = ctk.CTkImage(light_image=Image.open(screenshot_path), size=(220, 124))
                    self.app.image_label.configure(image=self.app.image_render)

            # Mettre à jour la frame précédente
            previous_frame = frame.copy()

            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            progress = self.get_video_progress(current_frame, total_frames)
            self.app.progress_bar.set(progress / 100)

        # Libérer les ressources
        cap.release()

        if (not self.stop): # Arrêté par fin de traitement
            app.end_process_dialog_event()


class ToplevelWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("300x150")

        self.label = ctk.CTkLabel(self, text="Traitement terminé")
        self.label.pack(padx=20, pady=20)

        self.button = ctk.CTkButton(self, text="Fermer", command=self.destroy)
        self.button.pack(pady=20)

        self.transient(self.master)
        self.grab_set()
        self.wait_window()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure appearance
        ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

        # Configure window
        self.geometry(f"{1100}x{580}")
        self.title("D'un Fragment à la Collection")

        # Configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=8, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="D'un Fragment à la Collection", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Apparance", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))

        self.scaling_label = ctk.CTkLabel(self.sidebar_frame, text="Interface", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")

        self.image_render = None

        self.image_label = ctk.CTkLabel(self.sidebar_frame, image=self.image_render, text="")
        self.image_label.grid(row=4, column=0, padx=20, pady=(20, 10))

        # Description - 0
        self.textbox_description = ctk.CTkLabel(self, justify="left", font=ctk.CTkFont(size=14),
            text="D'un Fragment à la Collection est un logiciel permettant d'extraire d'un film les différents plans qui le compose.\nSélectionnez la vidéo à traiter, le seuil de détection à appliquer et le dossier de sortie des images générées.")
        self.textbox_description.grid(row=0, column=1, columnspan=3, padx=(25, 20), pady=(5, 30), sticky="sw")

        # Chemin de la vidéo - 1, 2
        self.entry_video_path_description = ctk.CTkLabel(self, text="Récupérer le chemin de la vidéo à traiter :")
        self.entry_video_path_description.grid(row=1, column=1, padx=(25, 20), pady=(0, 0), sticky="sw")

        self.entry_video_path = ctk.CTkEntry(self, placeholder_text="Chemin de la vidéo")
        self.entry_video_path.grid(row=2, column=1, columnspan=2, padx=(20, 20), pady=(0, 0), sticky="ew")

        self.button_browse_video = ctk.CTkButton(self, text="Parcourir", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.browse_video)
        self.button_browse_video.grid(row=2, column=3, padx=(20, 20), pady=(0, 0))

        # Seuil de détection par slider - 3
        self.slider_progressbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.slider_progressbar_frame.grid(row=3, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.slider_progressbar_frame.grid_columnconfigure(0, weight=1)
        self.slider_progressbar_frame.grid_rowconfigure(4, weight=1)

        self.label_threshold = ctk.CTkLabel(self.slider_progressbar_frame, text="Seuil de détection (plus le seuil est bas, plus la tolérance est forte) :")
        self.label_threshold.grid(row=0, column=0, padx=(5, 20), pady=(0, 0), sticky="nsw")

        self.slider_threshold = ctk.CTkSlider(self.slider_progressbar_frame, orientation="horizontal", from_=0, to=1, number_of_steps=100, command=self.sliding)
        self.slider_threshold.grid(row=1, column=0, sticky="ew")
        self.slider_threshold.set(0.3)

        self.label_threshold_value = ctk.CTkLabel(self.slider_progressbar_frame, text="30%")
        self.label_threshold_value.grid(row=1, column=1, sticky="ew")

        # Chemin de sortie - 4, 5
        self.entry_video_path_description = ctk.CTkLabel(self, text="Spécifier où sera créé le dossier de sortie :")
        self.entry_video_path_description.grid(row=4, column=1, padx=(25, 20), pady=(0, 0), sticky="sw")

        self.entry_output_folder = ctk.CTkEntry(self, placeholder_text="Chemin du dossier de sortie")
        self.entry_output_folder.grid(row=5, column=1, columnspan=2, padx=(20, 20), pady=(0, 0), sticky="ew")

        self.button_browse_output_folder = ctk.CTkButton(master=self, text="Parcourir", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.browse_output_folder)
        self.button_browse_output_folder.grid(row=5, column=3, padx=(20, 20), pady=(0, 0))

        # Play/Stop - 6
        self.button_process_video = ctk.CTkButton(self, text="Lancer", command=self.process_video_thread)
        self.button_process_video.grid(row=6, column=3, padx=(20, 20), pady=(20, 5))
        self.button_stop_processing = ctk.CTkButton(self, text="Arrêter", command=self.stop_processing)
        self.button_stop_processing.grid(row=6, column=3, padx=(20, 20), pady=(20, 5))

        self.lancer_button_visible = False
        self.toggle_buttons()

        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal")
        self.progress_bar.grid(row=6, column=1, columnspan=2, padx=(20, 20), pady=(20, 20), sticky="ew")
        self.progress_bar.set(0)

        # Attribut pour stocker l'instance de la classe DetectChanges
        self.detect_changes = None

    def sliding(self, value):
        self.label_threshold_value.configure(text=str(int(value * 100)) + "%")

    def toggle_buttons(self):
        if self.lancer_button_visible:
            self.button_process_video.grid_forget()
            self.button_stop_processing.grid(row=6, column=3, padx=(20, 20), pady=(20, 5))
        else:
            self.button_stop_processing.grid_forget()
            self.button_process_video.grid(row=6, column=3, padx=(20, 20), pady=(20, 5))
        self.lancer_button_visible = not self.lancer_button_visible

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)

    def browse_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
        self.entry_video_path.delete(0, ctk.END)
        self.entry_video_path.insert(0, file_path)

    def browse_output_folder(self):
        folder_path = filedialog.askdirectory()
        self.entry_output_folder.delete(0, ctk.END)
        self.entry_output_folder.insert(0, folder_path)

    def process_video_thread(self):
        video_path = self.entry_video_path.get()
        output_folder = self.entry_output_folder.get()
        change_threshold = float(self.slider_threshold.get() * 100)

        if (video_path != "") and (output_folder != ""):
            self.detect_changes = DetectChanges(video_path, output_folder, change_threshold, self)
            threading.Thread(target=self.detect_changes.detect_changes).start()
            print("Traitement en cours...")
            self.toggle_buttons()
        else:
            print("Erreur : Veuillez renseigner le chemin de la vidéo et le dossier de sortie.")   

    def stop_processing(self):
        if self.detect_changes:
            self.detect_changes.stop = True  # Définit l'attribut stop à True pour arrêter le traitement
            print("Traitement arrêté.")
            self.toggle_buttons()
        else:
            print("Aucun traitement en cours.")

    def end_process_dialog_event(self):
        self.toggle_buttons()
        print("Traitement terminé.")
        # ToplevelWindow(self) # Fonctionne mais ne prend pas le focus ce qui est embêtant


# Lancement de la boucle principale
if __name__ == "__main__":
    app = App()
    app.mainloop()
