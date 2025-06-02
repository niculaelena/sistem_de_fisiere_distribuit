# Sistem distribuit de sincronizare a fișierelor

  

Acest proiect implementează un sistem simplu de sincronizare a fișierelor între client și server, folosind socket-uri și fire de execuție (multithreading) în Python.

  

## Funcționalități

  

- Sincronizează fișierele între mai mulți clienți și un server central

- Detectează modificările fișierelor (creare, modificare, ștergere, redenumire)

- Actualizări în timp real folosind un protocol personalizat peste TCP

- Codificare Base64 pentru transferul conținutului fișierelor

- Funcționează simultan cu mai multe directoare și clienți

  

## Structura proiectului

  

-  `server.py` – Serverul principal care stochează fișierele partajate și gestionează comunicarea cu clienții

-  `client.py` – Se conectează la server și menține sincronizat un folder local

-  `shared/` – Directorul central partajat de pe server

-  `client_data/` sau folder personalizat – Director local sincronizat pentru fiecare client

  

## Cum rulezi

  

### 1. Pornește serverul

  

```bash
python  server.py
```

  

Aceasta va crea folderul `shared/` dacă nu există deja.

  

### 2. Pornește un client

  

Poți specifica un folder pentru fiecare client (opțional):

  

```bash
python  client.py  client1_data
python  client.py  client2_data
```

  

Dacă nu specifici un folder, va folosi implicit `client_data`.

  

## Exemplu de utilizare

  

1. Rulează `server.py`

2. Rulează doi clienți în terminale separate:

```bash
python client.py client1_data
python client.py client2_data
```

3. Adaugă sau modifică fișiere într-unul dintre directoarele client.

4. Modificările vor fi sincronizate automat cu serverul și cu ceilalți clienți conectați.

  

## Observații

  

- Conținutul fișierelor este transferat folosind Base64 pentru a asigura transmiterea sigură.

- Sistemul suportă mai mulți clienți conectați simultan.