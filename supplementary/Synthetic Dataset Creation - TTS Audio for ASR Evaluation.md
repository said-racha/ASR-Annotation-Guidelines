To evaluate ASR model performance on edge cases not covered by the dataset FLEURS, we synthetically generated test cases covering specific scenarios like dates, currencies, hesitations, and inaudible segments. Below is the generation process:

          PROMPT → TTS → AUDIO → ASR MODELS → TRANSCRIPTIONS
              ↓                                      ↓
        [Text Corpus]                 [transcription_{lang}_synthetic.csv]

The text below is the *input* to TTS generation—it represents our curated test cases, not the actual model transcriptions. Each language section contains synthetic utterances designed to stress-test ASR systems on real-world phenomena.



Prompt :

```
Génére pour moi un nombre minimal de phrases en (Espagnol, Français, Portugais, Allemand) pour créer des audios de test TTS (Text-to-Speech) destinés à évaluer des modèles de transcription ASR. Les phrases doivent couvrir les cas de test suivants de manière réaliste et naturelle :

## 1. Monnaies et devises
- Inclure des monnaies avec symboles ($, €, £)
- Inclure des monnaies écrites en toutes lettres (euros, dollars, livres)

## 2. Dates et formats
- Différents formats de dates : "10 février 2023", "10/02/2023", "2023-02-10"
- Dates avec et sans année

## 3. Épellation de mots
- Phrases contenant des épellations : "Mon nom s'épelle D A N G"
- Épellations de noms propres ou codes

## 4. Abréviations informelles
- Utiliser des abréviations courantes (exemple : en anglais on dit "gonna" au lieu de "going to")

## 5. Hésitations et remplissage
- Inclure des "euh", "hum", "hmm" naturels
- Pauses de réflexion dans le discours

## 6. Sections inaudibles
- Indiquer des parties difficiles à entendre : "[inaudible]"

## 7. Autres éléments
- Adresses, numéros de téléphone
- Informations personnelles fictives

## Contraintes :
- Chaque phrase doit tenir sur moins de 30 secondes
- Mixer plusieurs cas de test dans une même phrase quand c'est naturel
- Ton conversationnel réaliste (comme un appel téléphonique ou un message vocal)
- Inclure une variété de contextes (appel client, rendez-vous, informations)
- Format de sortie : liste numérotée de phrases uniquement, sans explications
```


Text Corpus :

```
🇫🇷 Français

Bonjour, euh je vous appelle pour confirmer mon rendez-vous du 10 février 2023, enfin du 10/02/2023, pour 120 €, cent vingt euros, et mon nom s’épelle D A N G.

Alors voilà, mon code client c’est A B 1 2 3 4, faut que j’transfère 50 £, avant le 01 04 2024, enfin euh avant le 1er avril 2024. Hum, j’vais payer 3 dollars, le 5 mars sans l’année, à l’adresse 12 rue Victor Hugo 75015 Paris, mon téléphone c’est 06 12 34 56 78, mais j’ai entendu ksdhvkjscoqncdsienvcmlkjf.


🇪🇸 Español

Hola, eh te llamo pa’ confirmar mi cita del 10 de febrero de 2023, o sea 10/02/2023, por 200 €, doscientos euros, y mi nombre se escribe D A N G.

Bueno, mi código es X Y 9 8 7, tengo que pagar 75 £, setenta y cinco libras, antes del 5 de abril, vale, que si no me lo cobran ya. Hum, voy a mandar 500 dólares, el 2023 03 10, mi dirección es calle Mayor 15, Madrid 28013, y mi teléfono es 600 123 456, pero escuché ksdhvkjscoqncdsienvcmlkjf.


🇵🇹 Português

Olá, eu tô a ligar pra confirmar a reunião do dia 10 de fevereiro de 2023, quer dizer 10/02/2023, no valor de 250 €, duzentos e cinquenta euros, e o meu nome soletra-se D A N G.

O meu código é C D 5 6 7 8, preciso pagar 60 £, sessenta libras, até 01 05 2024, tá bom? Hum, vou transferir 400 dólares, no dia 2023-02-10, pra rua das Flores 20, Lisboa 1200-123, o meu telefone é 912 345 678, mas ouvi ksdhvkjscoqncdsienvcmlkjf.


🇩🇪 Deutsch

Hallo, äh ich ruf an wegen meinem Termin am 10. Februar 2023, also 10 02 2023, für 300 €, dreihundert Euro, und mein Name wird D A N G buchstabiert.

Mein Kundencode ist A B 1 2 3 4, ich muss 80 £, achtzig Pfund, bis zum 5. Mai zahlen, okay? Hm, ich werd 700 Dollar, am 2023-03-10 überweisen, meine Adresse ist Hauptstraße 25, 10115 Berlin, meine Telefonnummer ist 030 1234567, aber ich hab ksdhvkjscoqncdsienvcmlkjf gehört.


English
Hi, uh I’m gonna confirm my appointment on February 10, 2023, or 02 10 2023, for 250 $, two hundred fifty dollars, my name’s D A N G, and I gotta transfer 50 £, before 2023 02 15, but I heard ksdhvkjscoqncdsienvcmlkjf in your voicemail.


```

