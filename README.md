Projekt za ocjenjivanje ispita sa GUI suceljem

## Python verzija

- Koristen je Python 3.12.2

## Instalacija

```bash
pip install -r requirements.txt
```

> Napomena: projekt koristi samo standardnu biblioteku stoga mi je txt file requirements prazan.

## Pokretanje
Glavni ulaz je grader_project.py:

```bash
python grader_project.py
```

## Testovi
### Unittest

```bash
python -m unittest discover -s tests
```

### Doctest
```bash
python -m doctest -v grader_project.py
```

## Struktura projekta sastoji se od sljedecih fileova:
- `grader_project.py` – glavni dio gdje su mi dekoratori, closures, ABC, concurrency, unittest i koji sadrzi entry point za GUI.
- `gui_grader.py` – GUI aplikacija u Tkinteru koja koristi `grader_project`.
- `tests/test_ispiti_grader.py` – dodatni unit testovi.
- `requirements.txt` – nema vanjskih ovisnosti pa je prazan.

## Koristenje moje aplikacije
1. Moze se pokrenuti na dvije razlicite mape: jedna je studenti a jedna ispiti. Moguce je pokrenuti i na vlastitoj mapi ali je potrebno dodati JSON fileove nalik onima u mapama ispiti i studenti. Ovisno o mapi koja se koristi treba nastimati path. Trenutno se pokrece na mapi studenti
2. Pokrenuti: `python grader_project.py`.
3. Stisnuti gumb: Pocni s ocjenjivanjem
4. GUI ce tada prikazati tablicu rezultata koja ukljucuje imena studenata te broj bodova, ocjenu i prolaznost.
