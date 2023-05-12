# Chatidea

Chatidea è un framework che permette di generare chatbot partendo dallo schema
di una base di dati.

## Requisiti ed esecuzione chatbot

- [Python 3.7.6](https://www.python.org/downloads/release/python-376/)
- [Node.js](https://nodejs.org/it/)
- Installare chatito mediante il comando: `npm i chatito --save`
- Installare il gestore delle dipendenze PIP: se non si ha nessuna versione di
  pip installata bisogna prima scaricare il
  file [`get-pip.py`](https://bootstrap.pypa.io/get-pip.py) e lanciare il
  seguente comando dalla cartella dove avete scaricato il
  file: `python get-pip.py`
- Gestore delle dipendenze e ambienti virtuali installabile con
  comando `py -3.7 -m pip install pipenv` (in ambiente UNIX il comando `py`
  viene sostituito dal comando `python3`; se su windows non dovesse funzionare
  il comando `py` provare con `python`)
- Per installare tutte le dipendenze necessarie è sufficiente posizionarsi nella
  cartella `Chatidea` e lanciare i seguenti comandi in sequenza:
  ```shell
  SET PIPENV_VENV_IN_PROJECT=1 
  pipenv install
  ```
- Prima di lanciare il chatbot ricordare di avere sul proprio sistema attivo
  MySql e di aver installato il database di riferimento del chatbot (`deib` nel
  caso corrente il cui dump è disponibile nella
  cartella `Chatidea\resources\db`). Seguire gli step della configurazione per
  collegare il chatbot al database
- Per lanciare la chatbot dalla cartella `Chatidea` eseguire il
  comando `pipenv run python run.py`
- Dal browser ora il chabot è raggiungibile all’indirizzo http://localhost:5080

**NB:** In Windows potrebbero verificarsi problemi nell’installazione della
dipendenza ujson. Per risolvere tale problema bisogna installare gli strumenti
per VC++ del sistema operativo. Per fare questo, scaricare [*Microsoft Build
Tools
2015*](https://visualstudio.microsoft.com/it/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16)
Far partire l'installazione, al termine spuntare la casella "Strumenti di
compilazione C++" e selezionare i seguenti strumenti:

[![Aspose-Words-f23d8044-f5b5-4422-83f7-d7efd661b613-001.png](https://i.postimg.cc/0jLjf6ZR/Aspose-Words-f23d8044-f5b5-4422-83f7-d7efd661b613-001.png)](https://postimg.cc/T5JT23ZC)

Dopo aver selezionato tutti questi componenti procedere con l’installazione. A
installazione terminata, tornare nel prompt dei comandi e lanciare:

```shell
SET PIPENV_VENV_IN_PROJECT=1 
pipenv install
 ```

### Configurazione

Le variabili di configurazione sono all'interno di `Chatidea/settings.py`

```python
select = 'deib'

select_dict = {
  'teachers': ['b', 'teachers', '797397572:AAEV1MfR28lTzPsom_2qO2-goJSCKzQZ5d0'],
  'classicmodels': ['c', 'classicmodels', '710759393:AAGcrq2gkBd84qa-apwS9quMd5QK0knfWTM'],
  'deib': ['d', 'deib', '1046778538:AAF2CKzjxwzCu9fiDLgadBujYKuBKhgKmdE']
}
```

`select_dict` contiene una lista di database, è composto da: un carattere
identificativo, il nome dello schema, l'API Key del bot telegram. `select`
contiene il nome del database attualmente in uso.

```python
remote = True if os.environ.get('PYTHONANYWHERE_SITE') else False
DATABASE_USER = 'nicolacastaldo' if remote else 'root'
DATABASE_PASSWORD = 'dataexplorerbot' if remote else ''
DATABASE_HOST = 'nicolacastaldo.mysql.pythonanywhere-services.com' if remote else 'localhost'
DATABASE_NAME = 'nicolacastaldo$classicmodels' if remote else db_name
```

Cambiare user e password locali con i propri dati e, nel caso si voglia
utilizzare un host remoto, modificare opportunamente la variabile d'ambiente e i
dati restanti.

### Configurazione Webchat

In caso di utilizzo di `https` usare la parte di codice commentata e inserire
certificato e private key in `Chatidea/modules/connectors`.

```python
# sio = socketio.AsyncServer(cors_allowed_origins=[]) #Only for SSL workaround so that socketio works with requests from other origins.
sio = socketio.AsyncServer()


def start():
    # cert_path = os.path.dirname(os.path.realpath(__file__))
    # context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    # context.load_cert_chain(certfile=cert_path+ "/certificate.crt", keyfile= cert_path+"/private.key")
    # web.run_app(app, port=5080,ssl_context=context)
    web.run_app(app, port=5080)
```

Ricordare di cambiare il `socketUrl`
dentro `Chatidea/modules/connectors/index.html` inserendo http o https e la
porta giusta.

La libreria utilizzata per gestire la webchat non sembra più raggiungibile. In
alternativa potete usare:

```html
<script src="https://cdn.jsdelivr.net/npm/rasa-webchat/lib/index.min.js"></script>
```

Al posto di:

```html
<script src="https://storage.googleapis.com/mrbot-cdn/webchat-0.5.3.js"></script>
```

è necessario però modificare le personalizzazioni effettuate precedentemente
in* *index.html**adattandole alla nuova libreria.

### Come far partire il chatbot

Dentro `Chatidea/run.py` decommentare in base all'ambiente in cui si vuole
eseguire il chatbot.

```python
webchat.start()
# telegram.start()
# console_input()
```

In **locale** posizionatevi dentro `Chatidea` e eseguite il
comando `python run.py`

Per farlo partire su server Linux come servizio in background utilizzare `tmux`
per non far terminare l'esecuzione dello script a sessione
finita `tmux new -s <nome-sessione> python run.py`

Per riprendere il controllo della console dopo che si è
usciti: `tmux attach -t < nome-sessione>`

## Fasi per la generazione di un chatbot

Il processo di creazione di un nuovo chatbot può essere visto come una procedura
semi-automatica, essendo costituita da azioni automatiche e manuali. Le azioni
manuali sono quelle che dovranno essere svolte dal progettista e sono quelle che
interessano l’annotazione dei dati.

### Database schema

Creare un file JSON chiamato `db_schema_<carattere_identificativo>.json`
all'interno di `Chatidea/resources/db`. Il file contiene una descrizione
semplificata del database, evidenziandone la struttura in termini di attributi e
relazioni.

Esempio di come descrivere una tabella:

```json
{
  "location_locali": {
    "column_list": [
      "id_locale",
      "old_idlocale",
      "nomelocale",
      "descrizione",
      "id_edificio",
      "id_piano",
      "old_id_edificio",
      "old_id_piano",
      "passpartout",
      "is_laboratorio",
      "is_radl_richiesto",
      "is_user_richiedibile",
      "note_locale"
    ],
    "primary_key_list": [
      "id_locale"
    ],
    "references": [
      {
        "to_table": "location_edifici",
        "from_attribute": "id_edificio",
        "to_attribute": "id_edificio",
        "show_attribute": "nome_edificio"
      },
      {
        "to_table": "location_piani",
        "from_attribute": "id_piano",
        "to_attribute": "id_piano",
        "show_attribute": "descrizione_short"
      }
    ]
  }
}
```

In `references` si effettua il mapping della chiave esterna indicando la tabella
e l'attributo a cui è collegata. In `show_attribute` si indica un attributo da
mostrare al posto della chiave, che può risultare a volte poco significativa.

### Database concept

Creare un file JSON chiamato `db_concept_<carattere_identificativo>.json`
all'interno di `Chatidea/resources/db` e inserire una copia
chiamata `db_concept.json` all'interno di `Chatidea/static` ( serve per la
webchat)

Il file di concept rappresenta un punto cardine della progettazione, poiché
viene utilizzato sia per gestire la conversazione sia per generare le query.

```json
[
  {
    "element_name": "room",
    "aliases": [
      "rooms"
    ],
    "type": "secondary",
    "table_name": "location_locali",
    "show_columns": [
      {
        "keyword": "",
        "columns": [
          "descrizione"
        ]
      }
    ],
    "category": [],
    "attributes": [
      {
        "keyword": "",
        "type": "word",
        "columns": [
          "descrizione"
        ]
      },
      {
        "keyword": "in building",
        "type": "word",
        "columns": [
          "nome_edificio"
        ],
        "by": [
          {
            "from_table_name": "location_locali",
            "from_columns": [
              "id_edificio"
            ],
            "to_table_name": "location_edifici",
            "to_columns": [
              "id_edificio"
            ]
          }
        ]
      },
      {
        "keyword": "on floor",
        "type": "word",
        "columns": [
          "descrizione_short"
        ],
        "by": [
          {
            "from_table_name": "location_locali",
            "from_columns": [
              "id_piano"
            ],
            "to_table_name": "location_piani",
            "to_columns": [
              "id_piano"
            ]
          }
        ]
      }
    ],
    "relations": []
  }
]
```

- `element_name` indica come ci si deve riferire a una tabella durante la
  conversazione.
- `aliases` indica una serie di alternative che si possono utilizzare al posto
  dell'`element_name` all'interno della conversazione.
- `type` definisce il ruolo degli elementi nella conversazione. Una tabella
  contrassegnata come primary rappresenta un’informazione utile e indipendente
  dal contesto. Secondary identifica le tabelle i cui dati presi singolarmente
  non forniscono alcuna informazione, e pertanto per poter accedere ai loro dati
  si dovrà necessariamente passare da un’altra tabella. Crossable relations
  serve per contrassegnare le tabelle la cui relazione è molti-a-molti, questo
  tipo di tabelle infatti di solito presentano solo chiavi di altre tabelle, e
  senza un opportuno join le informazioni che contiene sarebbero prive di
  significato.
- `show_columns`. Quando il risultato di una query restituisce più di un
  risultato il chatbot li mostra in un listato di bottoni. Non essendo fattibile
  mostrare tutti gli attributi e non essendo la chiave primaria sempre
  identificativa in linguaggio naturale, bisogna indicare uno o più attributi
  che andranno mostrati in questa lista e che hanno il compito di rendere chiaro
  il contenuto del singolo risultato. Questa annotazione va effettuata solo per
  le tabelle identificate come primary e secondary.
- `category`. Per facilitare la navigazione dell'utente si può scegliere di
  categorizzare in base a una colonna una o più tabelle. Se una tabella primaria
  ha un attributo il cui valore può essere considerato una categoria da parte
  del progettista, questo attributo verrà utilizzato per mostrare alcune
  informazioni di riepilogo sulla tabella.
- `attributes`. Permette di definire i qualificatori conversazionali che
  l'utente può usare durante la conversazione. Il tipo di un qualificatore
  conversazionale può essere: WORD, NUM o DATE.

### Database view

Creare un file JSON chiamato `db_view_<carattere_identificativo>.json`
all'interno di `Chatidea/resources/db`.

```json
{
  "location_locali": {
    "column_list": [
      {
        "attribute": "descrizione",
        "display": "Name"
      },
      {
        "attribute": "id_edificio",
        "display": "Building"
      },
      {
        "attribute": "id_piano",
        "display": "Floor"
      },
      {
        "attribute": "note_locale",
        "display": "Notes"
      }
    ]
  }
}
```

Permette al progettista di indicare quali colonne mostrare di una specifica
tabella e di assegnare un alias da mostrare al posto del nome della colonna che
spesso risulta non essere significativa in linguaggio naturale.

### Generazione del modello

Generare il modello chatito con `python -m modules.translator`. Creare il
file `db_concept_s_<carattere_identificativo>` che permette di effettuare
l'autocompletamento in caso in cui l'utente non specifichi l'elemento di una
query. Il progettista, prendendo in riferimento gli attributi generati da
chatito, deve classificare le colonne delle tabelle in base a attributi simili.
Per esempio, gli attributi che fanno riferimento a un nome di persona fanno
parte della stessa categoria, gli attributi che fanno riferimento a un luogo
fanno parte di un'altra categoria e così via. Se una colonna non ha similarità
con altre colonne non va inserita nella tabella.

```json
[
  {
    "similars": [
      ["1_1", "3_3", "5_3"],
      ["1_2", "3_4", "4_2", "5_4"],
      ["1_3", "1_4"],
      ["1_5", "3_1"],
      ["1_6", "5_1"],
      ["4_3", "5_5"]
    ]
  }
]
```

Generare il training set
con: `cd writer && npx chatito chatito_model.chatito --format=rasa --defaultDistribution=even`.
Infine addestrare il modello: `python -m modules.trainer`

