# La migration d'un composant aussi complexe que smartdatetimectrl.py est une étape ambitieuse et très formatrice.
# Je suis là pour t'accompagner à chaque étape.
#
# Le fichier smartdatetimectrl.py est très bien écrit,
# mais il est profondément lié à wxPython.
# Il utilise des concepts comme le "Device Context" (dc)
# pour dessiner manuellement les composants,
# un système d'événements personnalisé,
# et des fenêtres popup spécifiques à wxPython.
# Une traduction ligne par ligne est donc impossible.
#
# Notre stratégie sera de recréer la fonctionnalité
# en utilisant les outils et la philosophie de Tkinter.
# Nous allons le faire pas à pas,
# en construisant une version claire, moderne et facile à maintenir.
#
# Plan de Développement
#
# Voici comment nous allons procéder pour transformer ce composant wxPython en un widget Tkinter :
#
#     Créer le Conteneur Principal (SmartDateTimeCtrl) : Ce sera un tkinter.Frame qui contiendra nos widgets de date et d'heure.
#
#     Construire les Champs de Saisie (Field) : Au lieu de dessiner le texte, nous utiliserons des widgets Tkinter. Le ttk.Spinbox est parfait pour les champs numériques (jour, mois, année, heure), car il gère la saisie numérique et les clics sur les flèches haut/bas. Pour les séparateurs (comme : ou /), nous utiliserons des ttk.Label.
#
#     Assembler les Entrées de Date et d'Heure (DateEntry, TimeEntry) : Nous créerons des classes qui assembleront les Spinbox et les Label dans le bon ordre, en se basant sur un format (par exemple, "jour/mois/année").
#
#     Gérer la Logique et les Événements : Nous connecterons la logique de validation (par exemple, un mois ne peut pas être supérieur à 12) et la navigation au clavier (passer d'un champ à l'autre avec les flèches).
#
#     Créer le Calendrier Popup (_CalendarPopup) : Ce sera la partie la plus complexe. Nous créerons une fenêtre tkinter.Toplevel qui s'affichera sous le champ de la date et contiendra des boutons pour chaque jour.
#
# Prêt à commencer ? Allons-y avec une première version qui couvre les étapes 1, 2 et 3.
#
# Étape 1 : Le Widget de Base en Tkinter
#
# Voici un premier code complet et fonctionnel. Il recrée le SmartDateTimeCtrl avec les champs de date et d'heure en utilisant des ttk.Spinbox. Il ne contient pas encore le calendrier popup, mais c'est une base solide et fonctionnelle que nous améliorerons ensemble.
#
# Analyse bien ce code, copie-le dans un fichier (par exemple, tkinter_datetime_ctrl.py) et exécute-le. Tu verras une fenêtre avec notre nouveau widget !

# Explication du Code
#
#     Classes de Widgets :
#
#         DateEntry, TimeEntry, et SmartDateTimeCtrl sont des classes qui héritent de ttk.Frame. C'est la manière standard de créer des widgets composés en Tkinter.
#
#         Le ttk est utilisé préférentiellement à tk car il offre des widgets plus modernes et mieux intégrés à l'apparence du système d'exploitation.
#
#     Variables de Contrôle (tk.IntVar) :
#
#         Au lieu de lire directement la valeur d'un widget, nous utilisons des tk.IntVar. Ces variables sont liées aux Spinbox via l'option textvariable.
#
#         L'avantage est double :
#
#             On peut obtenir ou définir la valeur du widget en manipulant la variable.
#
#             On peut "tracer" la variable (trace_add) pour déclencher une fonction (comme _validate_date) chaque fois que sa valeur est modifiée.
#
#     Validation de la Date (_validate_date) :
#
#         C'est la partie la plus "intelligente" de DateEntry. Elle utilise le module calendar de Python pour connaître le nombre de jours dans le mois/année sélectionné.
#
#         Elle met ensuite à jour la limite (to=...) du Spinbox du jour pour empêcher la sélection d'une date invalide (par exemple, le 31 février).
#
#     Événements Personnalisés (event_generate) :
#
#         Pour qu'un widget parent sache quand une valeur a changé dans un de ses enfants, nous utilisons des événements virtuels.
#
#         self.event_generate("<<DateChanged>>") crée un signal que le SmartDateTimeCtrl peut intercepter avec bind("<<DateChanged>>", ...). C'est une manière propre de faire communiquer les widgets entre eux.
#
#     Fenêtre de Démonstration (if __name__ == "__main__":) :
#
#         Cette partie ne s'exécute que si tu lances le fichier directement. Elle crée une petite fenêtre pour te montrer comment utiliser SmartDateTimeCtrl, comment lui donner une valeur initiale (set) et comment réagir à ses changements (bind).
#
# Prochaines Étapes
#
# Cette première version est déjà très puissante.
# Maintenant, je te propose de l'explorer.
# Regarde comment elle se comporte, essaie de changer les valeurs,
# et dis-moi ce que tu en penses.
#
# Une fois que cette base te convient, nous pourrons passer à l'étape suivante, qui est un défi intéressant : la création du calendrier popup.

#
# Excellente idée ! C'est une approche beaucoup plus moderne et intuitive pour l'utilisateur. Remplacer les trois Spinbox par un champ de saisie unique rend le composant plus compact et plus proche de ce qu'on a l'habitude de voir dans les applications web.
#
# Pour y arriver, nous allons modifier notre widget DateEntry :
#
#     Remplacer ttk.Spinbox par ttk.Entry : Nous utiliserons un champ de saisie de texte standard.
#
#     Mettre en place la validation : C'est le point crucial. Le widget doit être "intelligent". Il doit comprendre la chaîne de caractères que l'utilisateur tape (par exemple, "12/10/2025") et la valider.
#
#     Fournir un retour visuel : Si l'utilisateur saisit une date invalide (comme "99/10/2025"), le champ changera de couleur pour signaler l'erreur.
#
#     Ajouter un bouton pour le calendrier : À côté du champ de saisie, nous ajouterons un bouton. Pour l'instant, il sera inactif, mais c'est lui qui, à l'avenir, ouvrira notre calendrier popup.

# Ce qu'il faut observer
#
#     Le Champ de Saisie Unique : Tu as maintenant un seul champ pour la date, bien plus propre.
#
#     La Validation en Action :
#
#         Tape une date correcte comme 12/10/2025 et appuie sur Entrée ou clique ailleurs. Le champ reste normal.
#
#         Maintenant, tape une date volontairement fausse comme 32/10/2025 ou hello. Dès que tu quittes le champ, il devient rouge, te montrant instantanément qu'il y a un problème.
#
#     La Flexibilité du Format : Remarque que j'ai créé un deuxième contrôle (pnl2) avec un format différent (%Y-%m-%d). Cela montre que notre classe DateEntry est réutilisable et s'adapte à différents besoins.
#
#     Le Bouton Calendrier : Le petit bouton 📅 est là. Clique dessus : pour l'instant, il ne fait qu'afficher un message dans la console, mais il est prêt pour la suite.
#
# Cette base est bien plus robuste et conviviale. Manipule-la, teste-la et dis-moi si elle te convient.

#  La création du calendrier popup. C'est la partie la plus visuelle et interactive, et elle va vraiment donner vie à notre composant.
#
# Notre approche sera la suivante :
#
#     Créer une nouvelle classe CalendarPopup : Ce sera une fenêtre flottante (tkinter.Toplevel) qui contiendra notre calendrier.
#
#     Construire l'interface du calendrier : Elle inclura :
#
#         Des boutons de navigation ("<" et ">") pour changer de mois.
#
#         Un label affichant le mois et l'année en cours.
#
#         Une grille de boutons représentant les jours du mois.
#
#     Rendre le calendrier intelligent : Le calendrier devra savoir quel jour correspond à quel bouton et gérer les changements de mois.
#
#     Connecter le popup au DateEntry : Nous allons modifier la méthode _open_calendar de notre DateEntry pour qu'elle affiche cette nouvelle fenêtre popup juste en dessous du champ de saisie. Quand l'utilisateur cliquera sur un jour, la date sera automatiquement insérée dans le champ de texte.

# Explication des Nouveautés
#
#     CalendarPopup(tk.Toplevel) :
#
#         Hériter de Toplevel crée une nouvelle fenêtre indépendante.
#
#         self.overrideredirect(True) est la clé pour en faire un popup : cela supprime la barre de titre et les bordures de la fenêtre, lui donnant l'apparence d'un menu déroulant.
#
#         self.geometry(f"+{x}+{y}") permet de positionner la fenêtre exactement où l'on veut. On récupère les coordonnées du champ de texte (winfo_rootx, winfo_rooty) pour afficher le calendrier juste en dessous.
#
#         self.bind("<FocusOut>", ...) est un mécanisme de sécurité : si tu cliques n'importe où en dehors du calendrier, il se fermera automatiquement.
#
#     _populate_days() :
#
#         C'est le cœur de la logique du calendrier.
#
#         Il utilise calendar.monthcalendar() qui renvoie une liste de listes, représentant les semaines du mois. Les jours qui n'appartiennent pas au mois sont des 0.
#
#         Pour chaque jour valide, un ttk.Button est créé. La commande lambda d=day: self._select_date(d) est cruciale : elle permet de passer la valeur correcte du jour à la fonction de sélection.
#
#         Le bouton du jour actuel est mis en évidence avec un style ttk spécial pour une meilleure visibilité.
#
#     Intégration dans DateEntry :
#
#         La méthode _open_calendar est maintenant très simple : CalendarPopup(self.winfo_toplevel(), self). Elle crée une instance du popup.
#
#         Le popup reçoit une référence au widget DateEntry (self) pour pouvoir appeler sa méthode set() lorsqu'une date est choisie.
#
# Nous avons maintenant un composant SmartDateTimeCtrl complet, robuste et moderne pour Tkinter ! Il est facile à utiliser, flexible grâce au format de date personnalisable, et offre une excellente expérience utilisateur avec son champ de saisie intelligent et son calendrier popup.

# C'est une excellente stratégie pour faciliter la migration de ton application. En créant une "couche de compatibilité" où notre widget Tkinter expose les mêmes classes et noms de méthodes que la version wxPython, tu pourras réutiliser une grande partie de ton code existant avec un minimum de modifications.
#
# Nous allons donc adapter le code Tkinter précédent pour qu'il "imite" l'interface publique du smartdatetimectrl.py original.
#
# Les principaux changements que nous allons effectuer :
#
#     Renommer les méthodes : get() deviendra GetDateTime() et set(value) deviendra SetDateTime(value).
#
#     Ajouter la fonctionnalité enableNone : Nous allons intégrer une case à cocher (ttk.Checkbutton) qui permettra d'activer ou de désactiver le contrôle, et donc de retourner une valeur None.
#
#     Recréer la classe DateTimeSpanCtrl : Nous allons créer une classe de liaison qui gère la logique entre un contrôle de début et un contrôle de fin, exactement comme dans la version wxPython.
#
#     Ajouter des méthodes de compatibilité : Nous ajouterons des méthodes vides (comme EnableChoices ou Cleanup) pour que le code qui les appelle ne génère pas d'erreur, même si elles n'ont pas d'utilité dans notre version Tkinter.

# Comment l'utiliser
#
# Tu peux maintenant utiliser le SmartDateTimeCtrl en Tkinter de manière très similaire à la version wxPython :
#
#     Création : mon_controle = SmartDateTimeCtrl(parent, label="Date", enableNone=True)
#
#     Récupérer la valeur : valeur = mon_controle.GetDateTime()
#
#     Définir la valeur : mon_controle.SetDateTime(datetime.datetime(2025, 12, 25))
#
#     Gérer les changements :
#
#         Le système d'événements est la principale différence. Au lieu de EVT_DATETIME_CHANGE(ctrl, handler), tu utiliseras la méthode bind de Tkinter :
#         mon_controle.bind("<<DateTimeChanged>>", ma_fonction_handler)
#
#         Ta fonction ma_fonction_handler recevra un objet event de Tkinter. Tu peux accéder au widget qui a déclenché l'événement via event.widget.

#  Le comportement que tu décris est très fréquent lors de l'intégration d'une fenêtre popup (le calendrier) dans un système de contrôle de saisie (l'entrée de date).
#
# Le problème est que, si le clic sur la date aboutit à la même valeur que celle déjà affichée, notre fonction set précédente ne déclenchait pas d'événement de changement, car elle vérifiait si le texte avait réellement changé. Or, un clic explicite sur le calendrier est toujours considéré comme une action utilisateur qui doit être notifiée au contrôle parent.
#
# La solution est de modifier la méthode DateEntry.set pour qu'elle déclenche l'événement <<DateChanged>> de manière inconditionnelle après un clic sur le calendrier, car cet appel est le résultat direct d'une interaction utilisateur.
#
# Voici le code corrigé (seule la classe DateEntry est modifiée) :
#
# 🚀 Correction de la Gestion des Clics du Calendrier
#
# La modification est concentrée dans la méthode set de la classe DateEntry pour garantir que toute sélection de date provenant du calendrier propage bien l'événement de changement.

# Le fait que votre journal affiche des changements (Changement sur 'Début': 2025-10-12...) prouve que la logique interne et la propagation des événements fonctionnent, mais que la mise à jour visuelle du champ de saisie ne se fait pas immédiatement.
#
# Ceci est un problème classique en Tkinter impliquant les fenêtres Toplevel (le popup calendrier). Lorsque vous mettez à jour un widget de la fenêtre principale (DateEntry) juste avant de détruire une fenêtre secondaire (CalendarPopup), Tkinter peut ne pas avoir le temps de traiter la mise à jour visuelle avant que l'autre fenêtre ne soit fermée.
#
# 🚀 Correction de la Mise à Jour Visuelle
#
# La solution la plus fiable est de forcer Tkinter à traiter tous les événements en attente (comme la mise à jour de la zone de texte) juste après avoir défini la nouvelle date, mais avant de fermer la fenêtre popup.
#
# J'ai modifié la méthode CalendarPopup._select_date pour y ajouter l'appel à self.update_idletasks().

# Modifications apportées:
#
# Format de date pour tkcalendar: J'ai changé le date_pattern à '%Y-%m-%d' qui est un format standard et reconnu par tkcalendar   .
# Conversion de format lors de la sélection: Dans la méthode _select_date, après avoir récupéré la date sélectionnée avec self.cal.get_date(), je la convertis en un objet datetime en utilisant '%Y-%m-%d', puis je la reformate dans le format original (self.date_entry_widget.date_format) avant de la définir dans le DateEntry. Cela garantit que la date est affichée dans le format correct dans le champ de saisie.
#
# Autre approche (si vous voulez utiliser le format court/long de tkcalendar)

# Dans ce cas, vous n'avez pas besoin de convertir le format de date, car tkcalendar renvoie déjà la date dans un format compatible. Cependant, vous devrez vous assurer que le format court de tkcalendar correspond à ce que vous attendez.
import tkinter as tk
from tkinter import ttk
import datetime
import calendar  # à retirer si inutilisé
from tkcalendar import Calendar

# Pour s'assurer que les widgets ttk ont un joli look
from tkinter.font import Font


class CalendarPopup(tk.Toplevel):
    """
    Une fenêtre popup (Toplevel) qui affiche un calendrier pour sélectionner une date.
    """
    def __init__(self, parent, date_entry_widget, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.date_entry_widget = date_entry_widget
        self.selected_date = self.date_entry_widget.get() or datetime.date.today()
        self.current_year = self.selected_date.year
        self.current_month = self.selected_date.month

        # # --- Configuration de la fenêtre popup ---
        # self.overrideredirect(True)  # Supprime la barre de titre et les bordures
        # self.geometry(f"+{self.date_entry_widget.winfo_rootx()}+{self.date_entry_widget.winfo_rooty() + self.date_entry_widget.winfo_height()}")
        #
        # # Ferme le popup si on clique en dehors
        # self.bind("<FocusOut>", lambda e: self.destroy())
        # self.focus_set()
        #
        # # --- Création de l'interface du calendrier ---
        # self.main_frame = ttk.Frame(self, borderwidth=1, relief="solid")
        # self.main_frame.pack()

        # Use a date format that tkcalendar understands (e.g., '%Y-%m-%d')
        # self.cal = Calendar(self, selectmode="day", date_pattern=date_entry_widget.date_format)
        # self.cal = Calendar(self, selectmode="day", date_pattern='%Y-%m-%d')
        # # or Use the short date format of tkcalendar
        self.cal = Calendar(self, selectmode="day", date_pattern='short')
        self.cal.pack(fill="both", expand=True)
        ttk.Button(self, text="OK", command=self._select_date).pack()
        # Si vous utilisez une version plus ancienne de tkcalendar qui
        # nécessite un argument day, vous devrez modifier la fonction
        # _select_date pour accepter cet argument (même si vous ne l'utilisez pas)
        # comme ceci : def _select_date(self, day=None):

        # self._create_header()
        # self._create_day_names()
        # self.day_frame = ttk.Frame(self.main_frame)
        # self.day_frame.pack(pady=(0, 5), padx=5)
        # self._populate_days()

    def _create_header(self):
        """Crée l'en-tête avec les boutons de navigation et le mois/année."""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(pady=5, padx=5, fill='x')

        prev_button = ttk.Button(header_frame, text="<", command=self.prev_month, width=3)
        prev_button.pack(side="left")

        self.month_year_label = ttk.Label(
            header_frame,
            font=("TkDefaultFont", 10, "bold"),
            anchor="center"
        )
        self.month_year_label.pack(side="left", expand=True, fill='x')

        next_button = ttk.Button(header_frame, text=">", command=self.next_month, width=3)
        next_button.pack(side="right")

    def _create_day_names(self):
        """Crée les étiquettes pour les noms des jours (Lun, Mar, ...)."""
        names_frame = ttk.Frame(self.main_frame)
        names_frame.pack()

        # calendar.weekheader(2) -> 'Mo Tu We Th Fr Sa Su'
        for day_abbr in calendar.weekheader(2).split():
            ttk.Label(names_frame, text=day_abbr, width=4, anchor="center").pack(side="left")

    def _populate_days(self):
        """Remplit la grille avec les boutons des jours du mois en cours."""
        # On efface les anciens jours avant de redessiner
        for widget in self.day_frame.winfo_children():
            widget.destroy()

        # Mise à jour du label mois/année
        month_name = calendar.month_name[self.current_month]
        self.month_year_label.config(text=f"{month_name} {self.current_year}")

        # On récupère la matrice du calendrier
        month_calendar = calendar.monthcalendar(self.current_year, self.current_month)

        for week_num, week in enumerate(month_calendar):
            for day_num, day in enumerate(week):
                if day == 0: # Les jours qui n'appartiennent pas au mois
                    ttk.Label(self.day_frame, text="", width=4).grid(row=week_num, column=day_num)
                else:
                    day_button = ttk.Button(
                        self.day_frame,
                        text=str(day),
                        width=4,
                        command=lambda d=day: self._select_date(d)
                    )
                    day_button.grid(row=week_num, column=day_num, padx=1, pady=1)

                    # Mettre en surbrillance la date d'aujourd'hui
                    today = datetime.date.today()
                    if (self.current_year == today.year and
                            self.current_month == today.month and
                            day == today.day):
                        day_button.config(style="Today.TButton")

    # def _select_date(self, day):
    def _select_date(self):
        """Appelée quand un jour est cliqué. Met à jour l'Entry et ferme le popup."""
        # selected = datetime.date(self.current_year, self.current_month, day)
        # selected_date = self.cal.get_date()
        # self.date_entry_widget.set(selected)
        self.date_entry_widget.set(self.cal.get_date())
        # # Convert the selected date back to the original format
        # datetime_object = datetime.datetime.strptime(selected_date, '%Y-%m-%d').date()
        # self.date_entry_widget.set(datetime_object.strftime(self.date_entry_widget.date_format))
        # # # --- CORRECTION DE LA MISE À JOUR VISUELLE ---
        # # # Force Tkinter à traiter la mise à jour de la variable (entry_var.set)
        # # # avant de détruire la fenêtre.
        # # self.update_idletasks()
        # # # ---------------------------------------------

        self.destroy()

    def prev_month(self):
        """Passe au mois précédent."""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._populate_days()

    def next_month(self):
        """Passe au mois suivant."""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._populate_days()


# NOTE: Les classes DateEntry et TimeEntry sont maintenant considérées comme
# des composants internes de SmartDateTimeCtrl et n'ont pas besoin d'une API compatible.
class DateEntry(ttk.Frame):
    """
    Un widget pour saisir une date (jour, mois, année).
    """
    # def __init__(self, parent, *args, **kwargs):
    def __init__(self, parent, date_format='%d/%m/%Y', *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.date_format = date_format
        # Couleurs pour le retour visuel de la validation
        # self._valid_bg = ttk.Style().lookup("TEntry", "fieldbackground")
        # self._invalid_bg = "#ffdddd"  # Un rouge léger
        self._valid_bg, self._invalid_bg = ttk.Style().lookup("TEntry", "fieldbackground"), "#ffdddd"

        # # --- Variables pour stocker les valeurs ---
        # # On utilise les variables de contrôle de Tkinter pour lier
        # # facilement les valeurs aux widgets.
        self.year_var = tk.IntVar(value=datetime.date.today().year)
        self.month_var = tk.IntVar(value=datetime.date.today().month)
        self.day_var = tk.IntVar(value=datetime.date.today().day)

        # --- Variable de contrôle et widget d'entrée ---
        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(
            self,
            textvariable=self.entry_var,
            width=12,  # Assez large pour "jj/mm/aaaa"
            font=("TkDefaultFont", 11)
        )
        self.entry.pack(side='left', fill='x', expand=True)

        # --- Création des Widgets (Spinbox) ---
        # Le Spinbox est idéal car il limite la saisie aux chiffres
        # et permet d'incrémenter/décrémenter avec les flèches.

        # --- Bouton pour ouvrir le futur calendrier ---
        # Pour l'instant, il ne fait rien, mais il prépare le terrain.
        self.calendar_button = ttk.Button(
            self,
            text="📅",  # Emoji calendrier
            width=3,
            command=self._open_calendar  # Commande pour plus tard
        )
        self.calendar_button.pack(side='left', padx=(4, 0))

        # # Champ pour le jour
        # self.day_spinbox = ttk.Spinbox(
        #     self,
        #     from_=1,
        #     to=31,
        #     width=3,
        #     textvariable=self.day_var,
        #     command=self._on_change
        # )
        # self.day_spinbox.pack(side='left', padx=(0, 2))
        #
        # ttk.Label(self, text="/").pack(side='left', padx=(0, 2))
        #
        # # Champ pour le mois
        # self.month_spinbox = ttk.Spinbox(
        #     self,
        #     from_=1,
        #     to=12,
        #     width=3,
        #     textvariable=self.month_var,
        #     command=self._on_change
        # )
        # self.month_spinbox.pack(side='left', padx=(0, 2))
        #
        # ttk.Label(self, text="/").pack(side='left', padx=(0, 2))
        #
        # # Champ pour l'année
        # self.year_spinbox = ttk.Spinbox(
        #     self,
        #     from_=1900,
        #     to=2100,
        #     width=5,
        #     textvariable=self.year_var,
        #     command=self._on_change
        # )
        # self.year_spinbox.pack(side='left')

        # --- Lier les événements ---
        # --- Lier les événements pour la validation ---
        # # Quand une variable change, on valide la date
        # self.month_var.trace_add("write", self._validate_date)
        # self.year_var.trace_add("write", self._validate_date)
        # Valider quand l'utilisateur quitte le champ ou appuie sur Entrée.
        # Passage explicite de generate_event=True aux bindings utilisateurs
        # self.entry.bind("<FocusOut>", self._full_validate)
        self.entry.bind("<FocusOut>", lambda e: self._full_validate(event=e, generate_event=True))
        # self.entry.bind("<Return>", self._full_validate)
        self.entry.bind("<Return>", lambda e: self._full_validate(event=e, generate_event=True))
        # La trace est conservée, mais son effet est indirectement neutralisé par la correction ci-dessous.
        self.entry_var.trace_add("write", self._on_text_change)

    def _validate_date(self, *args):
        """Ajuste le nombre maximum de jours en fonction du mois et de l'année."""
        try:
            year = self.year_var.get()
            month = self.month_var.get()
            # calendar.monthrange donne le nombre de jours dans un mois
            # _, max_days = calendar.monthrange(year, month)
            _, max_days = Calendar.monthrange(year, month)
            # On met à jour la limite du spinbox des jours
            self.day_spinbox.config(to=max_days)

            # Si le jour actuel est supérieur au maximum, on l'ajuste
            if self.day_var.get() > max_days:
                self.day_var.set(max_days)

        except (tk.TclError, ValueError):
            # Arrive si le champ est vide ou invalide pendant la saisie
            pass

    # Tu as mis le doigt sur un problème classique et sournois en programmation,
    # souvent appelé récursion infinie ou boucle de validation.
    # Félicitations d'avoir isolé cette RecursionError : maximum recursion depth exceeded.
    #
    # Ce n'est pas un problème de la logique elle-même,
    # mais de la façon dont nous l'avons implémentée en Tkinter,
    # en mélangeant la lecture de la valeur (get) et la validation (_full_validate).
    #
    # 🛠️ Analyse de l'Erreur de Récursion
    #
    # L'erreur se produit à cause de la séquence d'appels suivante :
    #
    #     La fonction on_change (ton gestionnaire d'événement) appelle event.widget.GetDateTime().
    #
    #     SmartDateTimeCtrl.GetDateTime() appelle self.date_entry.get().
    #
    #     DateEntry.get() appelle self._full_validate(). 👈 C'est le point de départ de la boucle.
    #
    #     À l'intérieur de DateEntry._full_validate(), si la date est valide, le code fait ceci :
    #     Python
    #
    #     self.entry_var.set(formatted_date) # ❗ Étape critique
    #
    #     Problème : L'appel à self.entry_var.set() déclenche le "trace"
    #     (lié par self.entry_var.trace_add("write", self._on_text_change)),
    #     qui génère indirectement un nouvel événement de changement de la date
    #     (ou du moins, cela peut se propager).
    #
    #     Cet événement remonte et finit par rappeler ton gestionnaire on_change,
    #     et le cycle recommence : GetDateTime() -> get() -> _full_validate() -> set() -> Nouvel événement...
    #
    # Le système essaie de valider la date, et en la formatant
    # (même si elle ne change pas vraiment de valeur),
    # il déclenche à nouveau le mécanisme de validation,
    # conduisant à la récursion infinie.
    #
    # 💡 Correction et Code Simplifié
    #
    # Pour résoudre ce problème, nous devons
    # séparer clairement la lecture de la valeur de la validation qui modifie le champ.
    # La fonction de validation ne doit pas elle-même générer de nouveau changement de variable si ce n'est pas nécessaire.
    #
    # La solution la plus propre consiste à
    # conditionner la mise à jour de self.entry_var dans _full_validate()
    # pour ne la faire que si la valeur formatée diffère de la valeur actuelle.
    #
    # Voici la correction à apporter dans la classe DateEntry
    # (lignes 429-431 dans le fichier tkdatetimectrl.py fourni) :

    # Tu as encore mis le doigt sur un problème de récursion infinie,
    # qui est cette fois causé par le mélange entre la fonction qui lit la valeur (get)
    # et celle qui déclenche l'événement de changement.
    #
    # 🔍 Analyse et Correction de la Récursion
    #
    # L'erreur provient de la séquence d'appels suivante :
    #
    #     Un changement se produit (clic sur le calendrier, entrée au clavier, ou SetDateTime).
    #
    #     Le gestionnaire d'événement (on_change ou OnStartChange/OnEndChange) est appelé.
    #
    #     Le gestionnaire appelle SmartDateTimeCtrl.GetDateTime().
    #
    #     GetDateTime() appelle DateEntry.get().
    #
    #     DateEntry.get() appelle self._full_validate(). 👈 Le problème est là.
    #
    #     _full_validate() contient une ligne qui génère un nouvel événement self.event_generate("<<DateChanged>>").
    #
    #     Ce nouvel événement renvoie le contrôle au point 2, et le cycle se répète indéfiniment.
    #
    # Pour stopper cette boucle, nous devons
    # modifier les fonctions _full_validate et get
    # pour que la validation nécessaire à la lecture de la valeur ne déclenche JAMAIS un nouvel événement.
    #
    # 💡 Le Correctif
    #
    # Nous allons séparer la fonction de validation (qui formate le texte)
    # de la fonction qui génère l'événement de changement :
    #
    #     DateEntry._full_validate : Ajout d'un paramètre generate_event=True
    #     pour contrôler l'émission de l'événement.
    #
    #     DateEntry.get : Appelle _full_validate(generate_event=False)
    #     pour valider la valeur sans provoquer de boucle.
    #
    #     DateEntry.set : Est simplifiée pour ne générer l'événement
    #     que si la valeur a effectivement changé, réduisant ainsi le risque de récursion.
    # def _full_validate(self, event=None):
    def _full_validate(self, event=None, generate_event=True):
        """
        Valide la date complète lorsque l'utilisateur a fini de taper.

         Le drapeau `generate_event` empêche la récursion.
        """
        try:
            # On essaie de convertir le texte en date avec le format fourni
            text = self.entry_var.get()
            if not text:  # Si le champ est vide, c'est valide (pas de date)
                self.entry.config(background=self._valid_bg)
                return True

            date_obj = datetime.datetime.strptime(text, self.date_format).date()
            # Si la conversion réussit, on reformate le texte pour être propre
            # Ex: "1/1/25" pourrait devenir "01/01/2025"
            formatted_date = date_obj.strftime(self.date_format)

            # self.entry_var.set(formatted_date)
            # --- CORRECTION DE L'ERREUR DE RÉCURSION ---
            # Correction de la récursion lors du formatage
            # On met à jour self.entry_var SEULEMENT si le texte formaté
            # est différent du texte actuel.
            if self.entry_var.get() != formatted_date:
                # Si la valeur change, cela déclenchera le trace, mais la prochaine
                # validation (récursive) n'entrera plus dans cette condition.
                self.entry_var.set(formatted_date)
            # -------------------------------------------

            # Le fond redevient normal
            self.entry.config(background=self._valid_bg)

            # self.event_generate("<<DateChanged>>")
            # --- CORRECTION DE LA RÉCURSION : Événement généré SEULEMENT si demandé ---
            if generate_event:
                self.event_generate("<<DateChanged>>")
            return True

        except ValueError:
            # Si strptime échoue, la date est invalide
            self.entry.config(background=self._invalid_bg)
            return False

    def _on_text_change(self, *args):
        """Remet la couleur de fond à la normale pendant que l'utilisateur tape."""
        # C'est une simple mise à jour visuelle, elle n'appelle pas _full_validate
        self.entry.config(background=self._valid_bg)

    def get(self):
        """
        Retourne la date sous forme d'objet datetime.date ou None si invalide.

        Récupère la valeur. Appelle la validation SANS générer d'événement.
        """
        # # Cette méthode déclenche toujours la validation complète.
        # # try:
        # #     return datetime.date(
        # #         self.year_var.get(), self.month_var.get(), self.day_var.get()
        # #     )
        # # except (tk.TclError, ValueError):
        # #     return None # Retourne None si la date est invalide
        # if self._full_validate():
        # --- CORRECTION DE LA RÉCURSION : generate_event=False est crucial ---
        if self._full_validate(generate_event=False):
            try:
                return datetime.datetime.strptime(self.entry_var.get(), self.date_format).date()
            except ValueError:
                return None
        return None

    def set(self, date_obj):
        """
        Définit la date à partir d'un objet datetime.date
        et déclenche l'événement uniquement si la valeur change.

        Déclenche l'événement inconditionnellement car
        cet appel est considéré comme une action utilisateur intentionnelle (calendrier).
        """
        # if isinstance(date_obj, datetime.date):
        #     # self.year_var.set(date_obj.year)
        #     # self.month_var.set(date_obj.month)
        #     # self.day_var.set(date_obj.day)
        #     # self._validate_date()
        #     formatted_date = date_obj.strftime(self.date_format)
        # new_text = ""
        # if isinstance(date_obj, datetime.date):
        #     new_text = date_obj.strftime(self.date_format)

        # current_text = self.entry_var.get()
        #
        # if current_text != new_text:
        #     # self.entry_var.set(formatted_date)
        # Mise à jour de la variable sans vérification de changement de texte,
        # car on assume un changement intentionnel (clic calendrier).
        # L'événement est généré ici pour assurer que le clic calendrier
        # est bien propagé au SmartDateTimeCtrl.
        # self.entry_var.set(new_text)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, date_obj)
        # self.entry.config(background=self._valid_bg)
        # # L'événement est généré ici pour les changements programmatiques
        # self.event_generate("<<DateChanged>>")  # Notifier le changement
        # elif date_obj is None:
        #     self.entry_var.set("")
        #     # self.entry.config(background=self._valid_bg)

        # # On valide la nouvelle valeur et on génère l'événement si tout est OK
        # if self._full_validate():
        #     # Assure que le fond est correct et que l'événement a été généré
        #     pass

    def _on_change(self):
        """Génère un événement virtuel lorsque la valeur change."""
        self.event_generate("<<DateChanged>>")

    def _open_calendar(self):
        """
        Ouvre le popup du calendrier.

        Cette fonction sera connectée au calendrier popup dans la prochaine étape.
        """
        print("Le bouton du calendrier a été cliqué ! Prochaine étape : afficher le popup.")
        # C'est ici que nous instancierons et afficherons notre Toplevel de calendrier.
        CalendarPopup(self.winfo_toplevel(), self)

    def set_state(self, state):
        self.entry.config(state=state)
        self.calendar_button.config(state=state)


class TimeEntry(ttk.Frame):
    """
    Un widget pour saisir une heure (heure, minute, seconde).
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # --- Variables pour stocker les valeurs ---
        now = datetime.datetime.now().time()
        self.hour_var = tk.IntVar(value=now.hour)
        self.minute_var = tk.IntVar(value=now.minute)
        self.second_var = tk.IntVar(value=now.second)

        # --- Création des Widgets ---
        self.hour_spinbox = ttk.Spinbox(
            self, from_=0, to=23, width=3, textvariable=self.hour_var, command=self._on_change, format="%02.0f"
        )
        self.hour_spinbox.pack(side='left', padx=(0, 2))

        ttk.Label(self, text=":").pack(side='left', padx=(0, 2))

        self.minute_spinbox = ttk.Spinbox(
            self, from_=0, to=59, width=3, textvariable=self.minute_var, command=self._on_change, format="%02.0f"
        )
        self.minute_spinbox.pack(side='left', padx=(0, 2))

        ttk.Label(self, text=":").pack(side='left', padx=(0, 2))

        self.second_spinbox = ttk.Spinbox(
            self, from_=0, to=59, width=3, textvariable=self.second_var, command=self._on_change, format="%02.0f"
        )
        self.second_spinbox.pack(side='left')

    def get(self):
        """Retourne l'heure sous forme d'objet datetime.time."""
        # try:
        #     return datetime.time(
        #         self.hour_var.get(), self.minute_var.get(), self.second_var.get()
        #     )
        # except (tk.TclError, ValueError):
        #     return None
        h = self.hour_spinbox.get()
        m = self.minute_spinbox.get()
        s = self.second_spinbox.get()
        if h and m and s:
            return f"{int(h):02}:{int(m):02}:{int(s):02}"
        else:
            return None

    def set(self, time_obj):
        """
        Définit l'heure à partir d'un objet datetime.time,

        génère l'événement SEULEMENT si l'heure change.
        """
        # # if isinstance(time_obj, datetime.time):
        # #     self.hour_var.set(time_obj.hour)
        # #     self.minute_var.set(time_obj.minute)
        # #     self.second_var.set(time_obj.second)
        # if isinstance(time_obj, datetime.time):
        #     current_time = self.get()
        #
        #     # --- CORRECTION : Vérifie si la valeur change avant de générer l'événement ---
        #     if current_time != time_obj:
        #         self.hour_var.set(time_obj.hour)
        #         self.minute_var.set(time_obj.minute)
        #         self.second_var.set(time_obj.second)
        #         self.event_generate("<<TimeChanged>>")
        #         # Si l'heure est la même, on ne fait rien, empêchant le rebond.
        if time_obj:
            h, m, s = map(int, time_obj.split(':'))
            self.hour_spinbox.delete(0, tk.END)
            self.hour_spinbox.insert(0, f"{h:02}")
            self.minute_spinbox.delete(0, tk.END)
            self.minute_spinbox.insert(0, f"{m:02}")
            self.second_spinbox.delete(0, tk.END)
            self.second_spinbox.insert(0, f"{s:02}")
        else:
            self.hour_spinbox.delete(0, tk.END)
            self.minute_spinbox.delete(0, tk.END)
            self.second_spinbox.delete(0, tk.END)

    def _on_change(self):
        """Génère un événement virtuel lorsque la valeur change."""
        self.event_generate("<<TimeChanged>>")

    def set_state(self, state):
        for child in self.winfo_children():
            try: child.config(state=state)
            except tk.TclError: pass


# --- CLASSE PRINCIPALE AVEC API COMPATIBLE WXPYTHON --- #
class SmartDateTimeCtrl(ttk.Frame):
    """
    Le widget principal qui combine la saisie de la date et de l'heure.

    Widget de date/heure pour Tkinter avec une API compatible
    avec la version wxPython de smartdatetimectrl.
    """
    # def __init__(self, parent, label=None, *args, **kwargs):
    # def __init__(self, parent, label=None, date_format='%d/%m/%Y', *args, **kwargs):
    def __init__(self, parent, value=None, label="", enableNone=False, date_format='%d/%m/%Y', timeFormat=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # if label:
        #     ttk.Label(self, text=label).pack(side='left', padx=(0, 5))
        self.date_format = date_format
        self._is_enabled = True

        # --- Gestion de `enableNone` ---
        self.enableNone = enableNone
        self.value = None  # Stocke un objet datetime ou None

        col = 0  # Suivre la colonne actuelle

        if self.enableNone:
            self.check_var = tk.BooleanVar()
            self.checkbox = ttk.Checkbutton(self, text=label, variable=self.check_var, command=self._on_toggle_none)
            # self.checkbox.pack(side='left', padx=(0, 5))
            self.checkbox.grid(row=0, column=col, sticky="w")
            col += 1
        # elif label:
        if label:
            # ttk.Label(self, text=label).pack(side='left', padx=(0, 5))
            # ttk.Label(self, text=label).grid(row=0, column=0, sticky="w")
            ttk.Label(self, text=label).grid(row=0, column=col, sticky="w")
            col += 1

        # --- Création des widgets internes ---
        # Le formatage de l'heure n'est pas utilisé ici car TimeEntry a un format fixe,
        # mais le paramètre est conservé pour la compatibilité.
        # self.date_entry = DateEntry(self)
        # self.date_entry = DateEntry(self, date_format=date_format)
        self.date_entry = DateEntry(self, date_format=self.date_format)
        # self.date_entry.pack(side='left', padx=(0, 5))
        self.date_entry.grid(row=0, column=col, sticky="ew")
        col += 1

        self.time_entry = TimeEntry(self)
        # self.time_entry.pack(side='left')
        self.time_entry.grid(row=0, column=col, sticky="ew")
        col += 1

        # # Lier les événements des sous-widgets à un événement global
        # self.date_entry.bind("<<DateChanged>>", self._on_change)
        # self.time_entry.bind("<<TimeChanged>>", self._on_change)

        # --- Initialisation de la valeur ---
        # self.SetDateTime(value if value is not None else datetime.datetime.now())
        # if self.enableNone and value is None:
        #     self.check_var.set(False)
        #     self.Enable(False)
        # elif self.enableNone:
        #     self.check_var.set(True)
        # if enableNone:
        #     self.none_var = tk.BooleanVar()
        #     self.none_check = ttk.Checkbutton(self, text="Aucun", variable=self.none_var, command=self._on_none_check)
        #     # self.none_check.grid(row=0, column=3, sticky="w")
        #     self.none_check.grid(row=0, column=col, sticky="w")
        # On utilise SetDateTime pour initialiser et gérer le cas None/enableNone
        self.SetDateTime(value)  # Initialisation avec la valeur

        # Configurer le redimensionnement des colonnes
        self.columnconfigure(col, weight=1)  # La dernière colonne s'étend

    def get(self):
        """Retourne la date et l'heure combinées en objet datetime.datetime."""
        date = self.date_entry.get()
        time = self.time_entry.get()
        if date and time:
            return datetime.datetime.combine(date, time)
        return None

    def GetDateTime(self):
        """Récupère et retourne la date/heure actuelle sous forme d'objet datetime.

        Retourne None si enableNone est True et que la case est cochée.
        Compatible avec l'API wxPython."""
        # if not self._is_enabled:
        # if self.enable_none and self.none_var.get():
        if self.enableNone and self.check_var.get():
            return None
        # # self.get()
        # date = self.date_entry.get()
        # time = self.time_entry.get()
        # if date and time:
        #     return datetime.datetime.combine(date, time)
        # return None
        try:
            date_value = self.date_entry.get()
            time_value = self.time_entry.get()

            if date_value and time_value:
                datetime_string = f"{date_value} {time_value}"
                return datetime.datetime.strptime(datetime_string, f"{self.date_format} %H:%M:%S")
            else:
                return None  # date ou heure invalide
        except ValueError:
            return None  # format invalide

    def set(self, datetime_obj):
        """Définit la date et l'heure à partir d'un objet datetime.datetime."""
        if isinstance(datetime_obj, datetime.datetime):
            self.date_entry.set(datetime_obj.date())
            self.time_entry.set(datetime_obj.time())

    def SetDateTime(self, value, notify=False):
        """Définit la date/heure. Accepte un objet datetime ou None.

        Compatible avec l'API wxPython."""
        self.value = value  # Stockage interne de la valeur

        # is_datetime = isinstance(value, datetime.datetime)
        # # if isinstance(value, datetime.datetime):
        # if is_datetime:
        #     # self.set(value)
        #     self.Enable(True)
        #     self.date_entry.set(value.date())
        #     self.time_entry.set(value.time())
        #     if self.enableNone:
        #         self.check_var.set(True)
        # elif value is None and self.enableNone:
        #     self.Enable(False)
        #     # self.check_var.set(False)
        #     self.date_entry.set(None) # Vider le champ de date
        #     if self.enableNone:
        #         self.check_var.set(False)
        #
        # # Si on ne passe pas de datetime/None, on ne fait rien ou on initialise à l'heure actuelle
        # elif value is None and not self.enableNone:
        #     # Initialisation par défaut si pas de valeur fournie et pas de None autorisé
        #     self.SetDateTime(datetime.datetime.now(), notify=False)
        if value is None and self.enableNone:
            # self.none_var.set(True)
            self.check_var.set(True)
            self.date_entry.set("")
            self.time_entry.set("")
        else:
            if value:
                # self.none_var.set(False)
                self.check_var.set(False)
                self.date_entry.set(value.strftime(self.date_format))
                self.time_entry.set(value.strftime("%H:%M:%S"))
            else:
                self.date_entry.set("")
                self.time_entry.set("")

        # if notify:
        #     self._on_internal_change()

    def Enable(self, enabled=True):
        """Active ou désactive le contrôle. Compatible avec l'API wxPython."""
        self._is_enabled = enabled
        state = 'normal' if enabled else 'disabled'
        self.date_entry.set_state(state)
        self.time_entry.set_state(state)

        # S'assurer que la checkbox reste active si enableNone est utilisé
        if self.enableNone:
            self.checkbox.config(state='normal')

    def _on_toggle_none(self):
        """Gère le clic sur la case à cocher `enableNone`.

        Gère le changement d'état de la case à cocher "Aucun".
        """
        # self.Enable(self.check_var.get())
        # self._on_internal_change()

        # if self.none_var.get():
        if self.check_var.get():
            self.date_entry.set("")
            self.time_entry.set("")
        else:
            if self.value:
                self.SetDateTime(self.value)

    def _on_internal_change(self, event=None):
        """Génère un événement pour le widget principal."""
        self.event_generate("<<DateTimeChanged>>")

    def _on_change(self, event=None):
        """Génère un événement virtuel pour le widget principal."""
        self.event_generate("<<DateTimeChanged>>")

    # --- Méthodes de compatibilité vides ---
    def Cleanup(self):
        """
        Méthode de compatibilité (wxPython).  Ne fait rien.
        """
        pass

    def EnableChoices(self, enable=True):
        """
        Méthode de compatibilité (wxPython). Ne fait rien.
        """
        pass

    def SetRelativeChoicesStart(self, start=None): pass

    def LoadChoices(self, choices): pass


# --- CLASSE DE LIAISON COMPATIBLE WXPYTHON --- #
# class DateTimeSpanCtrl:
class DateTimeSpanCtrl(ttk.Frame):
    """
    Un contrôle pour sélectionner un intervalle de date/heure.

    Lie deux SmartDateTimeCtrl pour gérer un intervalle de temps,
    en assurant une durée minimale. Compatible avec l'API wxPython.
    """
    def __init__(self, parent, ctrlStart, ctrlEnd, minSpan=None):
        super().__init__(parent)  # Initialiser ttk.Frame
        label_start="Début"
        label_end="Fin"
        self.__ctrlStart = ctrlStart
        self.__ctrlEnd = ctrlEnd
        self.__minSpan = minSpan

        self.__ctrlStart.EnableChoices()
        self.__ctrlEnd.EnableChoices()
        self.__ctrlEnd.SetRelativeChoicesStart(self.__ctrlStart.GetDateTime())

        ttk.Label(self, text=label_start).grid(row=0, column=0, sticky="w")
        self.start_datetime = SmartDateTimeCtrl(self)
        self.start_datetime.grid(row=0, column=1, sticky="ew")

        ttk.Label(self, text=label_end).grid(row=1, column=0, sticky="w")
        self.end_datetime = SmartDateTimeCtrl(self)
        self.end_datetime.grid(row=1, column=1, sticky="ew")

        self.__ctrlStart.bind("<<DateTimeChanged>>", self.OnStartChange)
        self.__ctrlEnd.bind("<<DateTimeChanged>>", self.OnEndChange)

        # Initialiser pour vérifier la cohérence après la création
        self.OnStartChange()

    def OnStartChange(self, event=None):
        start_dt = self.__ctrlStart.GetDateTime()
        end_dt = self.__ctrlEnd.GetDateTime()

        if start_dt and end_dt and self.__minSpan:
            # Si le début dépasse la fin, ou si l'intervalle est trop court,
            # on ajuste la fin pour maintenir l'intervalle minimum.
            if start_dt + self.__minSpan > end_dt:
                # SetDateTime est appelé avec notify=True par défaut, ce qui déclenchera OnEndChange.
                # self.__ctrlEnd.SetDateTime(start_dt + self.__minSpan)
                self.__ctrlEnd.SetDateTime(start_dt + self.__minSpan, notify=True)

    def OnEndChange(self, event=None):
        start_dt = self.__ctrlStart.GetDateTime()
        end_dt = self.__ctrlEnd.GetDateTime()

        if start_dt and end_dt and self.__minSpan:
            # Si la fin est avant le début + l'intervalle minimum,
            # on ajuste la fin pour respecter l'intervalle.
            if end_dt < start_dt + self.__minSpan:
                # On ne modifie pas le début, on invalide la fin en la réajustant.
                # SetDateTime est appelé avec notify=True par défaut, ce qui déclenchera OnStartChange.
                # Cependant, puisque la valeur est déjà fixée par OnStartChange,
                # la correction ci-dessus dans DateEntry empêchera la récursion.
                # self.__ctrlEnd.SetDateTime(start_dt + self.__minSpan)
                self.__ctrlEnd.SetDateTime(start_dt + self.__minSpan, notify=True)

    def GetStartDateTime(self):
        return self.start_datetime.GetDateTime()

    def GetEndDateTime(self):
        return self.end_datetime.GetDateTime()

    def SetStartDateTime(self, dt):
        self.start_datetime.SetDateTime(dt)

    def SetEndDateTime(self, dt):
        self.end_datetime.SetDateTime(dt)


# --- Fenêtre de démonstration ---
if __name__ == "__main__":

    def on_datetime_change(event):
        """Fonction appelée lorsque la date ou l'heure change."""
        # dt = pnl1.get()
        dt = pnl1.GetDateTime()
        if dt:
            print(f"Nouvelle date/heure : {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            # Mettre à jour l'étiquette avec la nouvelle valeur
            result_label.config(text=f"Valeur sélectionnée : {dt.strftime('%c')}")
        else:
            result_label.config(text="Valeur sélectionnée : Date invalide")

        dt_start = spanCtrl.GetStartDateTime()
        dt_end = spanCtrl.GetEndDateTime()

        print("Start date:", dt_start)
        print("End date:", dt_end)

    root = tk.Tk()
    root.title("Test du SmartDateTimeCtrl en Tkinter")

    # Style pour une apparence plus moderne
    style = ttk.Style(root)
    # Tente d'utiliser un thème plus esthétique s'il est disponible
    # ('clam', 'alt', 'default' sur Windows, 'aqua' sur macOS)
    if 'clam' in style.theme_names():
        style.theme_use('clam')

    # # Augmenter la taille de la police pour une meilleure lisibilité
    # # default_font = Font(font=ttk.Style().lookup("TSpinbox", "font"))
    # default_font = Font(font=style.lookup("TLabel", "font"))
    # default_font.config(size=11)
    # # style.configure("TSpinbox", font=default_font)
    # style.configure("TLabel", font=default_font)
    # style.configure("TButton", font=default_font)
    # Style spécial pour le bouton "aujourd'hui"
    style.configure("Today.TButton", bordercolor="blue", font=("TkDefaultFont", 9, "bold"))

    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill='both', expand=True)

    # --- Création de notre widget ---
    # --- Utilisation de l'API compatible ---
    # On utilise le format jour/mois/année
    # pnl1 = SmartDateTimeCtrl(main_frame, label="Début :")
    # pnl1 = SmartDateTimeCtrl(main_frame, label="Début :", date_format='%d/%m/%Y')
    pnl1 = SmartDateTimeCtrl(main_frame, label="Début :", enableNone=True, value=None)
    # pnl1.pack(pady=(0, 10), anchor='w')
    pnl1.pack(pady=5, anchor='w')

    # # Initialiser avec une date spécifique
    # initial_datetime = datetime.datetime(2025, 10, 26, 10, 30, 0)
    # pnl1.set(initial_datetime)

    # --- Un deuxième widget pour montrer la flexibilité du format ---
    # On utilise le format américain année-mois-jour
    pnl2 = SmartDateTimeCtrl(main_frame, label="Fin :", date_format='%Y-%m-%d')
    # pnl2.pack(pady=(0, 10), anchor='w')
    pnl2.pack(pady=5, anchor='w')
    # pnl2.set(datetime.datetime.now())  # Initialiser avec la date/heure actuelle

    # Lier les deux contrôles avec un intervalle minimum d'une heure
    spanCtrl = DateTimeSpanCtrl(main_frame, pnl1, pnl2, minSpan=datetime.timedelta(hours=1))
    spanCtrl.pack()

    def on_change(event):
        widget_name = "Début" if event.widget == pnl1 else "Fin"
        dt = event.widget.GetDateTime()  # On utilise la méthode compatible
        print(f"Changement sur '{widget_name}': {dt}")

    # # Lier l'événement personnalisé
    # pnl1.bind("<<DateTimeChanged>>", on_datetime_change)
    pnl1.bind("<<DateTimeChanged>>", on_change)
    pnl2.bind("<<DateTimeChanged>>", on_change)

    # Définir une valeur initiale
    # pnl1.set(datetime.datetime.now())  # Initialiser avec la date du jour
    pnl1.SetDateTime(datetime.datetime.now())

    # Une étiquette pour afficher le résultat
    result_label = ttk.Label(main_frame, text="Valeur sélectionnée : ...")
    result_label.pack(pady=10, anchor='w')

    # # Mettre à jour l'étiquette au démarrage
    # on_datetime_change(None)

    root.mainloop()
