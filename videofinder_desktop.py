#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VidéoFinder v1 - Desktop Application
Gestionnaire de favoris vidéo avec interface graphique
Compatible avec PyInstaller pour conversion en .exe
"""

import PySimpleGUI as sg
import json
import os
import webbrowser
import subprocess
import platform
from datetime import datetime
from pathlib import Path

# ─── CONFIGURATION ───
PIN_CORRECT = '2187'
DATA_DIR = Path.home() / '.videofinder'
DATA_DIR.mkdir(exist_ok=True)

LS_SITES = DATA_DIR / 'sites.json'
LS_FAVS = DATA_DIR / 'favs.json'
LS_HIST = DATA_DIR / 'history.json'
LS_THEME = DATA_DIR / 'theme.json'
MAX_HIST = 20

# ─── THÈMES COULEURS ───
DARK_THEME = {
    'bg': '#1c1b19',
    'surface': '#201f1d',
    'surface2': '#2d2c2a',
    'border': '#3a3836',
    'text': '#e8e5df',
    'muted': '#b5b0a7',
    'faint': '#878177',
    'primary': '#4f98a3',
    'primary_d': '#2f7b86',
    'success': '#79b454',
    'warning': '#e2a94a',
    'error': '#dd6da8',
}

LIGHT_THEME = {
    'bg': '#f7f6f2',
    'surface': '#ffffff',
    'surface2': '#f0ede8',
    'border': '#dcd9d5',
    'text': '#28251d',
    'muted': '#676661',
    'faint': '#8a8882',
    'primary': '#01696f',
    'primary_d': '#0c4e54',
    'success': '#437a22',
    'warning': '#b7791f',
    'error': '#a12c7b',
}

# ─── UTILITAIRES ───
def load_json(path, default=None):
    """Charge un fichier JSON."""
    if default is None:
        default = []
    try:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return default

def save_json(path, data):
    """Sauvegarde des données en JSON."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur de sauvegarde: {e}")

def load_theme():
    """Charge le thème sauvegardé."""
    theme_name = load_json(LS_THEME, 'dark')
    return DARK_THEME if theme_name == 'dark' else LIGHT_THEME

def save_theme(theme_name):
    """Sauvegarde le thème."""
    save_json(LS_THEME, theme_name)

def open_url(url):
    """Ouvre une URL dans le navigateur."""
    if url:
        webbrowser.open(url, new=2)

# ─── APPLICATION ───
class VidéoFinderApp:
    def __init__(self):
        self.sites = load_json(LS_SITES, [])
        self.favs = load_json(LS_FAVS, [])
        self.history = load_json(LS_HIST, [])
        self.current_theme = load_theme()
        self.current_cat = 'Tous'
        self.search_query = ''
        self.edit_index = -1
        self.current_tab = 'search'
        self.pin_value = ''
        self.authenticated = False
        
        sg.theme_background_color(self.current_theme['bg'])
        sg.theme_text_color(self.current_theme['text'])
        sg.theme_element_background_color(self.current_theme['surface'])
        sg.theme_input_background_color(self.current_theme['surface2'])
        sg.theme_input_text_color(self.current_theme['text'])
        sg.theme_button_color((self.current_theme['text'], self.current_theme['primary']))
        
    def get_categories(self):
        """Retourne les catégories uniques."""
        cats = set()
        for site in self.sites:
            if site.get('categorie'):
                cats.add(site['categorie'])
        return ['Tous'] + sorted(list(cats))
    
    def is_favorite(self, url):
        """Vérifie si un site est favori."""
        return any(f['url'] == url for f in self.favs)
    
    def get_fav_index(self, url):
        """Récupère l'index d'un favori."""
        for i, f in enumerate(self.favs):
            if f['url'] == url:
                return i
        return -1
    
    def add_to_history(self, site):
        """Ajoute un site à l'historique."""
        if not site.get('url'):
            return
        self.history.insert(0, {
            **site,
            'visited_at': datetime.now().isoformat()
        })
        self.history = self.history[:MAX_HIST]
        save_json(LS_HIST, self.history)
    
    def get_filtered_sites(self):
        """Retourne les sites filtrés."""
        result = self.sites.copy()
        
        if self.current_cat != 'Tous':
            result = [s for s in result if s.get('categorie') == self.current_cat]
        
        if self.search_query:
            q = self.search_query.lower()
            result = [s for s in result if
                     q in (s.get('nom') or '').lower() or
                     q in (s.get('url') or '').lower() or
                     q in (s.get('description') or '').lower() or
                     q in (s.get('categorie') or '').lower()]
        
        return result
    
    def create_pin_layout(self):
        """Crée l'interface PIN."""
        layout = [
            [sg.Text('🎬', font=('Arial', 48), justification='center', key='-PIN_ICON-')],
            [sg.Text('VidéoFinder v1', font=('Arial', 20, 'bold'), justification='center')],
            [sg.Text('Entrez votre code PIN\npour accéder au gestionnaire de favoris',
                    font=('Arial', 11), justification='center', size=(40, 2))],
            [sg.Text('●' * len(self.pin_value) + '○' * (4 - len(self.pin_value)),
                    font=('Arial', 16), justification='center', key='-PIN_DOTS-', size=(20, 1))],
            [sg.Column([
                [sg.Button('1', size=(6, 3), key='-PIN_1-'),
                 sg.Button('2', size=(6, 3), key='-PIN_2-'),
                 sg.Button('3', size=(6, 3), key='-PIN_3-')],
                [sg.Button('4', size=(6, 3), key='-PIN_4-'),
                 sg.Button('5', size=(6, 3), key='-PIN_5-'),
                 sg.Button('6', size=(6, 3), key='-PIN_6-')],
                [sg.Button('7', size=(6, 3), key='-PIN_7-'),
                 sg.Button('8', size=(6, 3), key='-PIN_8-'),
                 sg.Button('9', size=(6, 3), key='-PIN_9-')],
                [sg.Button('⌫', size=(6, 3), key='-PIN_DEL-'),
                 sg.Button('0', size=(6, 3), key='-PIN_0-'),
                 sg.Button('✓', size=(6, 3), key='-PIN_OK-')],
            ], vertical_alignment='center', horizontal_alignment='center')],
            [sg.Text('', font=('Arial', 10), text_color=self.current_theme['error'],
                    key='-PIN_ERROR-', justification='center', size=(40, 1))],
        ]
        return layout
    
    def create_search_layout(self):
        """Crée l'interface de recherche."""
        filtered = self.get_filtered_sites()
        
        categories = self.get_categories()
        
        site_elements = []
        for i, site in enumerate(filtered):
            idx = self.sites.index(site)
            is_fav = self.is_favorite(site['url'])
            url_short = (site.get('url') or '').replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
            
            card = [
                sg.Frame('', [
                    [sg.Text('🌐', font=('Arial', 14)), 
                     sg.Text(site.get('nom', 'Sans nom'), font=('Arial', 11, 'bold')),
                     sg.Text(site.get('categorie', ''), font=('Arial', 8), text_color=self.current_theme['muted'])],
                    [sg.Text(url_short, font=('Arial', 9), text_color=self.current_theme['muted'])],
                    [sg.Text(site.get('description', ''), font=('Arial', 9), text_color=self.current_theme['faint'], size=(30, 2))],
                    [sg.Button('🌐 Ouvrir', key=f'-OPEN_{idx}-', size=(8, 1)),
                     sg.Button('★' if is_fav else '☆', key=f'-FAV_{idx}-', size=(3, 1)),
                     sg.Button('✏', key=f'-EDIT_{idx}-', size=(3, 1)),
                     sg.Button('🗑', key=f'-DEL_{idx}-', size=(3, 1)),
                     sg.Button('↗', key=f'-SHARE_{idx}-', size=(3, 1))],
                ], border_width=1, element_justification='left')
            ]
            site_elements.append(card)
        
        if not site_elements:
            site_elements = [
                [sg.Text('Aucun site enregistré', font=('Arial', 14, 'bold'), justification='center')],
                [sg.Text('Cliquez sur "Ajouter" pour commencer', font=('Arial', 11), justification='center')],
                [sg.Button('➕ Ajouter un site', key='-ADD_EMPTY-')],
            ]
        
        layout = [
            [sg.Text(f'{len(filtered)} site(s)', font=('Arial', 9), text_color=self.current_theme['muted'])],
            [sg.InputText(placeholder_text='Rechercher...', key='-SEARCH-', size=(30, 1)),
             sg.Combo(categories, default_value=self.current_cat, key='-CAT_FILTER-', readonly=True),
             sg.Button('🔍', key='-SEARCH_BTN-')],
            [sg.Combo(categories, default_value=self.current_cat, key='-CAT_CHIPS-', readonly=True,
                     enable_events=True)],
            [sg.Column(site_elements, scrollable=True, vertical_scroll_only=True,
                      size=(600, 400), key='-SITES_SCROLL-')],
        ]
        return layout
    
    def create_favs_layout(self):
        """Crée l'interface des favoris."""
        fav_elements = []
        for i, fav in enumerate(self.favs):
            fav_elements.append([
                sg.Text(f"⭐ {fav.get('nom')}", font=('Arial', 11, 'bold')),
                sg.Button('🌐', key=f'-FAV_OPEN_{i}-', size=(3, 1)),
                sg.Button('↗', key=f'-FAV_SHARE_{i}-', size=(3, 1)),
                sg.Button('🗑', key=f'-FAV_DEL_{i}-', size=(3, 1)),
            ])
        
        if not fav_elements:
            fav_elements = [[sg.Text('Aucun favori', font=('Arial', 12), justification='center')]]
        
        layout = [
            [sg.Text('Vos sites favoris', font=('Arial', 14, 'bold'))],
            [sg.Column(fav_elements, scrollable=True, vertical_scroll_only=True,
                      size=(600, 400), key='-FAVS_SCROLL-')],
        ]
        return layout
    
    def create_history_layout(self):
        """Crée l'interface de l'historique."""
        hist_elements = []
        for i, item in enumerate(self.history):
            date = item.get('visited_at', '')[0:10]
            hist_elements.append([
                sg.Text(f"🕐 {item.get('nom')}", font=('Arial', 11)),
                sg.Text(date, font=('Arial', 9), text_color=self.current_theme['muted']),
                sg.Button('🌐', key=f'-HIST_OPEN_{i}-', size=(3, 1)),
            ])
        
        if not hist_elements:
            hist_elements = [[sg.Text('Aucun historique', font=('Arial', 12), justification='center')]]
        
        layout = [
            [sg.Text('Historique de navigation', font=('Arial', 14, 'bold'))],
            [sg.Column(hist_elements, scrollable=True, vertical_scroll_only=True,
                      size=(600, 400), key='-HIST_SCROLL-')],
        ]
        return layout
    
    def create_settings_layout(self):
        """Crée l'interface des paramètres."""
        theme_name = 'sombre' if load_json(LS_THEME, 'dark') == 'dark' else 'clair'
        
        layout = [
            [sg.Text('Paramètres', font=('Arial', 14, 'bold'))],
            [sg.Text('Thème', font=('Arial', 11, 'bold'))],
            [sg.Radio('🌙 Mode sombre', 'theme', default=(theme_name == 'sombre'),
                     key='-THEME_DARK-'), 
             sg.Radio('☀️ Mode clair', 'theme', default=(theme_name == 'clair'),
                     key='-THEME_LIGHT-')],
            [sg.Button('Appliquer', key='-APPLY_THEME-', size=(15, 1))],
            [sg.Text('')],
            [sg.Text('Données', font=('Arial', 11, 'bold'))],
            [sg.Button('📊 Exporter les données', key='-EXPORT_DATA-', size=(20, 1))],
            [sg.Button('📥 Importer les données', key='-IMPORT_DATA-', size=(20, 1))],
            [sg.Button('🗑 Effacer tous les sites', key='-CLEAR_ALL-', size=(20, 1))],
            [sg.Text('')],
            [sg.Text('À propos', font=('Arial', 11, 'bold'))],
            [sg.Text('VidéoFinder v1', font=('Arial', 10, 'bold'))],
            [sg.Text('Gestionnaire de favoris vidéo', font=('Arial', 9, 'italic'))],
        ]
        return layout
    
    def run(self):
        """Lance l'application."""
        # Écran PIN
        pin_window = sg.Window(
            'VidéoFinder v1 - Authentification',
            self.create_pin_layout(),
            size=(500, 600),
            background_color=self.current_theme['bg'],
            text_color=self.current_theme['text'],
            no_titlebar=False,
            finalize=True
        )
        
        while True:
            event, values = pin_window.read(timeout=100)
            
            if event == sg.WINDOW_CLOSED:
                pin_window.close()
                return
            
            if event and event.startswith('-PIN_'):
                if event == '-PIN_DEL-':
                    self.pin_value = self.pin_value[:-1]
                elif event == '-PIN_OK-':
                    if len(self.pin_value) == 4:
                        if self.pin_value == PIN_CORRECT:
                            self.authenticated = True
                            break
                        else:
                            sg.popup_error('Code PIN incorrect!', title='Erreur')
                            self.pin_value = ''
                elif event in ['-PIN_0-', '-PIN_1-', '-PIN_2-', '-PIN_3-', '-PIN_4-',
                               '-PIN_5-', '-PIN_6-', '-PIN_7-', '-PIN_8-', '-PIN_9-']:
                    if len(self.pin_value) < 4:
                        digit = event[-2]
                        self.pin_value += digit
                
                pin_window['-PIN_DOTS-'].update('●' * len(self.pin_value) + '○' * (4 - len(self.pin_value)))
        
        pin_window.close()
        
        # Fenêtre principale
        self.main_window()
    
    def main_window(self):
        """Fenêtre principale de l'application."""
        tab_group = sg.TabGroup([
            [sg.Tab('🔍 Recherche', self.create_search_layout(), key='-TAB_SEARCH-'),
             sg.Tab('⭐ Favoris', self.create_favs_layout(), key='-TAB_FAVS-'),
             sg.Tab('🕐 Historique', self.create_history_layout(), key='-TAB_HISTORY-'),
             sg.Tab('⚙️ Paramètres', self.create_settings_layout(), key='-TAB_SETTINGS-')],
        ], key='-TAB_GROUP-', tab_location='bottom')
        
        layout = [
            [sg.Text('🎬 VidéoFinder v1', font=('Arial', 16, 'bold')),
             sg.Button('➕ Ajouter', key='-ADD_SITE-'),
             sg.Button('Quitter', key='-QUIT-')],
            [tab_group],
            [sg.Text('', key='-STATUS-', size=(50, 1), text_color=self.current_theme['success'])],
        ]
        
        window = sg.Window(
            'VidéoFinder v1',
            layout,
            size=(700, 600),
            background_color=self.current_theme['bg'],
            text_color=self.current_theme['text'],
            finalize=True
        )
        
        while True:
            event, values = window.read(timeout=100)
            
            if event == sg.WINDOW_CLOSED or event == '-QUIT-':
                break
            
            if not event:
                continue
            
            # Recherche
            if event == '-SEARCH-' or event == '-SEARCH_BTN-':
                self.search_query = values['-SEARCH-'].strip()
                window['-TAB_SEARCH-'].update(self.create_search_layout())
            
            if event == '-CAT_FILTER-' or event == '-CAT_CHIPS-':
                self.current_cat = values['-CAT_FILTER-'] or values['-CAT_CHIPS-']
                window['-TAB_SEARCH-'].update(self.create_search_layout())
                window['-CAT_FILTER-'].update(self.current_cat)
                window['-CAT_CHIPS-'].update(self.current_cat)
            
            # Ajouter site
            if event == '-ADD_SITE-' or event == '-ADD_EMPTY-':
                self.show_add_modal(window)
                window['-TAB_SEARCH-'].update(self.create_search_layout())
                window['-TAB_FAVS-'].update(self.create_favs_layout())
            
            # Ouvrir site
            if event.startswith('-OPEN_'):
                try:
                    idx = int(event.split('_')[1].rstrip('-'))
                    if 0 <= idx < len(self.sites):
                        self.add_to_history(self.sites[idx])
                        open_url(self.sites[idx].get('url'))
                        window['-STATUS-'].update('✓ Site ouvert dans le navigateur')
                except (ValueError, IndexError):
                    pass
            
            # Favoris
            if event.startswith('-FAV_'):
                parts = event.split('_')
                if len(parts) >= 3:
                    action = parts[1]
                    try:
                        idx = int(parts[2].rstrip('-'))
                        if action == 'DEL' and 0 <= idx < len(self.sites):
                            fi = self.get_fav_index(self.sites[idx]['url'])
                            if fi >= 0:
                                self.favs.pop(fi)
                                save_json(LS_FAVS, self.favs)
                                window['-TAB_SEARCH-'].update(self.create_search_layout())
                                window['-TAB_FAVS-'].update(self.create_favs_layout())
                                window['-STATUS-'].update('✓ Retiré des favoris')
                        elif action == 'OPEN' and 0 <= idx < len(self.favs):
                            self.add_to_history(self.favs[idx])
                            open_url(self.favs[idx].get('url'))
                            window['-STATUS-'].update('✓ Site ouvert')
                    except (ValueError, IndexError):
                        pass
            
            # Éditer/Supprimer
            if event.startswith('-EDIT_'):
                try:
                    idx = int(event.split('_')[1].rstrip('-'))
                    self.show_edit_modal(window, idx)
                    window['-TAB_SEARCH-'].update(self.create_search_layout())
                except (ValueError, IndexError):
                    pass
            
            if event.startswith('-DEL_'):
                try:
                    idx = int(event.split('_')[1].rstrip('-'))
                    if 0 <= idx < len(self.sites):
                        if sg.popup_yes_no(f"Supprimer '{self.sites[idx]['nom']}'?") == 'Yes':
                            self.sites.pop(idx)
                            save_json(LS_SITES, self.sites)
                            window['-TAB_SEARCH-'].update(self.create_search_layout())
                            window['-STATUS-'].update('✓ Site supprimé')
                except (ValueError, IndexError):
                    pass
            
            # Paramètres
            if event == '-APPLY_THEME-':
                theme = 'dark' if values['-THEME_DARK-'] else 'light'
                save_theme(theme)
                window['-STATUS-'].update('✓ Thème changé. Redémarrez l\'app.')
            
            if event == '-CLEAR_ALL-':
                if sg.popup_yes_no('Effacer tous les sites?') == 'Yes':
                    self.sites = []
                    self.favs = []
                    save_json(LS_SITES, self.sites)
                    save_json(LS_FAVS, self.favs)
                    window['-TAB_SEARCH-'].update(self.create_search_layout())
                    window['-STATUS-'].update('✓ Données effacées')
        
        window.close()
    
    def show_add_modal(self, parent_window):
        """Affiche le dialogue d'ajout."""
        layout = [
            [sg.Text('Ajouter un site', font=('Arial', 12, 'bold'))],
            [sg.Text('Nom du site:'), sg.InputText(key='-ADD_NOM-', size=(30, 1))],
            [sg.Text('URL:'), sg.InputText(key='-ADD_URL-', size=(30, 1))],
            [sg.Text('Catégorie:'), sg.Combo(self.get_categories(), key='-ADD_CAT-', size=(27, 1))],
            [sg.Text('Description:'), sg.Multiline(size=(30, 3), key='-ADD_DESC-')],
            [sg.Button('Enregistrer', key='-SAVE_ADD-'),
             sg.Button('Annuler', key='-CANCEL_ADD-')],
        ]
        
        window = sg.Window(
            'Ajouter un site',
            layout,
            background_color=self.current_theme['bg'],
            text_color=self.current_theme['text'],
            modal=True
        )
        
        while True:
            event, values = window.read()
            
            if event == sg.WINDOW_CLOSED or event == '-CANCEL_ADD-':
                break
            
            if event == '-SAVE_ADD-':
                if not values['-ADD_NOM-'] or not values['-ADD_URL-']:
                    sg.popup_error('Remplissez tous les champs obligatoires!')
                    continue
                
                self.sites.append({
                    'nom': values['-ADD_NOM-'],
                    'url': values['-ADD_URL-'],
                    'categorie': values['-ADD_CAT-'],
                    'description': values['-ADD_DESC-'],
                })
                save_json(LS_SITES, self.sites)
                break
        
        window.close()
    
    def show_edit_modal(self, parent_window, idx):
        """Affiche le dialogue d'édition."""
        if idx < 0 or idx >= len(self.sites):
            return
        
        site = self.sites[idx]
        
        layout = [
            [sg.Text('Modifier le site', font=('Arial', 12, 'bold'))],
            [sg.Text('Nom du site:'), sg.InputText(site.get('nom', ''), key='-EDIT_NOM-', size=(30, 1))],
            [sg.Text('URL:'), sg.InputText(site.get('url', ''), key='-EDIT_URL-', size=(30, 1))],
            [sg.Text('Catégorie:'), sg.Combo(self.get_categories(), site.get('categorie', ''),
                    key='-EDIT_CAT-', size=(27, 1))],
            [sg.Text('Description:'), sg.Multiline(site.get('description', ''),
                    size=(30, 3), key='-EDIT_DESC-')],
            [sg.Button('Enregistrer', key='-SAVE_EDIT-'),
             sg.Button('Annuler', key='-CANCEL_EDIT-')],
        ]
        
        window = sg.Window(
            'Modifier le site',
            layout,
            background_color=self.current_theme['bg'],
            text_color=self.current_theme['text'],
            modal=True
        )
        
        while True:
            event, values = window.read()
            
            if event == sg.WINDOW_CLOSED or event == '-CANCEL_EDIT-':
                break
            
            if event == '-SAVE_EDIT-':
                self.sites[idx] = {
                    'nom': values['-EDIT_NOM-'],
                    'url': values['-EDIT_URL-'],
                    'categorie': values['-EDIT_CAT-'],
                    'description': values['-EDIT_DESC-'],
                }
                save_json(LS_SITES, self.sites)
                break
        
        window.close()


# ─── POINT D'ENTRÉE ───
if __name__ == '__main__':
    app = VidéoFinderApp()
    app.run()
