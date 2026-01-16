
import spacy
import warnings
import pytest

import medspacy

LANGUAGE_CODE = 'fr'

class TestPipelineFR:
    def test_create_pipeline(self):
        nlp = medspacy.load(language_code = LANGUAGE_CODE)

        assert nlp

    def test_default_components(self):
        nlp = medspacy.load(language_code = LANGUAGE_CODE)

        nlp.add_pipe("medspacy_sectionizer", config = {'language_code': LANGUAGE_CODE})

        doc = nlp("""Examen physique: Normale
        
                Aucune maladies""")

        assert doc
        assert len(doc._.sections) > 0
