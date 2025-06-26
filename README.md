[en] This is a web-based database for societies, clubs and accociations. Until now it is only available with the frontend in german language. If you want to make a translation please feel free to contact me.[/en]

# MemberBase
Online Mitglieder-Datenbank und Mitgliederverwaltung für Vereine

## Beta-Status

Diese Software ist im __Beta-Stadium__.
Alle wirklich wichtigen Features sind implementiert und werden gerade im Produktivbetrieb getestet.

## Installation

Auf einem Debian(-basierten) System kann als `root` die `install.sh`-Datei ausgeführt werden:

Mit `sudo chmod +x install.sh` ausführbar machen, dann mit `./install.sh` ausführen.

Updates werden genauso installiert.

MemberBase läuft dann als system-Service und ist im Browser auf dem Server unter `http://localhost:4208` aufrufbar.

Für externen Zugriff ist ein ReverseProxy wie z.B. `nginx` zu installieren, der sinnvollerweise auch die Verschlüsselung z.B. mit Let's Encrypt-Zertifikat übernimmt. Anleitungen dazu finden sich reichlich im Netz oder es lässt sich mit Hilfe des Lieblings-Spachmodells umsetzen.
