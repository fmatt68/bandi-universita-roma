# Bandi Università Roma

Monitoraggio automatico dei bandi universitari pubblicati dagli atenei di Roma.

Il progetto utilizza script Python e GitHub Actions per individuare nuove procedure pertinenti, controllarne la scadenza e inviare una notifica via email.

## Obiettivo

Il repository monitora principalmente:

- docenze e incarichi di insegnamento;
- docenti a contratto;
- professori di prima fascia;
- professori di seconda fascia;
- manifestazioni di interesse per attività didattiche;
- opportunità scientifiche e biomediche selezionate.

I criteri possono variare in base alla struttura e ai contenuti pubblicati da ciascun ateneo.

## Atenei ed enti monitorati

Il workflow controlla attualmente:

- Sapienza Università di Roma;
- Università degli Studi di Roma Tor Vergata;
- Università degli Studi Roma Tre;
- Università Cattolica del Sacro Cuore, sede di Roma;
- Fondazione Policlinico Universitario Agostino Gemelli IRCCS;
- Università LUMSA;
- UniCamillus;
- Università Campus Bio-Medico di Roma;
- Link Campus University.

È inoltre presente uno script diagnostico per l’Università Europea di Roma.

Il monitor UER è temporaneamente escluso dal workflow perché il sito e le API possono essere bloccati da sistemi di verifica anti-bot.

## Link Campus University

Il monitor Link Campus University controlla le procedure per:

- professori di prima fascia;
- professori ordinari;
- professori di seconda fascia;
- professori associati.

Sono considerate soltanto le procedure:

- appartenenti alle aree scientifiche e biomediche di interesse;
- con sede di lavoro a Roma, oppure senza una sede esterna chiaramente indicata;
- ancora aperte alla data dell’esecuzione;
- non già segnalate in precedenza.

Il monitor esclude:

- ricercatori a tempo determinato;
- verbali;
- commissioni giudicatrici;
- approvazioni degli atti;
- graduatorie;
- convocazioni;
- rinvii delle sedute;
- regolamenti e documenti accessori.

La futura comparsa di bandi per docenze a contratto potrà essere gestita con un parser dedicato.

## Aree disciplinari

I monitor selezionano principalmente procedure appartenenti ad aree come:

- biologia;
- biologia molecolare e cellulare;
- biotecnologie;
- biochimica;
- genetica;
- genetica medica;
- immunologia;
- microbiologia;
- patologia;
- farmacologia;
- fisiologia;
- oncologia;
- ematologia;
- neuroscienze;
- medicina;
- chirurgia;
- statistica medica;
- informatica e bioinformatica;
- fisica applicata alle scienze della vita.

Quando disponibili, vengono utilizzati anche i codici dei gruppi e dei settori scientifico-disciplinari, tra cui:

- BIOS;
- MEDS;
- MEDF;
- IINF;
- PHYS;
- BIO;
- MED;
- FIS;
- ING-INF.

## Funzionamento

Ogni monitor esegue, in generale, queste operazioni:

1. scarica la pagina ufficiale dei bandi;
2. individua le procedure potenzialmente pertinenti;
3. esclude documenti accessori e fasi successive della selezione;
4. estrae titolo, tipologia, area disciplinare e scadenza;
5. elimina le procedure già scadute;
6. confronta i risultati con il relativo file storico;
7. invia un’email in presenza di nuove procedure;
8. aggiorna lo storico soltanto dopo l’invio riuscito dell’email.

## File storici

Ogni fonte utilizza un file JSON per evitare notifiche duplicate.

Esempi:

```text
storico.json
storico_cattolica.json
storico_gemelli.json
storico_linkcampus.json
storico_lumsa.json
storico_romatre.json
storico_torvergata.json
storico_unicamillus.json
storico_unicampus.json
