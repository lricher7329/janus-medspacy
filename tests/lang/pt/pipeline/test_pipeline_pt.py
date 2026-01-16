
import spacy
import warnings
import pytest

import medspacy

LANGUAGE_CODE = 'pt'

class TestPipelinePT:
    def test_create_pipeline(self):
        nlp = medspacy.load(language_code = LANGUAGE_CODE)

        assert nlp

    def test_default_components(self):
        nlp = medspacy.load(language_code = LANGUAGE_CODE)

        nlp.add_pipe("medspacy_sectionizer", config = {'language_code': LANGUAGE_CODE})

        doc = nlp("""Resumo da Consulta Médica

                Data da Consulta: 14 de Maio de 2024
                Nome do Paciente: burgersmoke""")

        assert doc
        assert len(doc._.sections) > 0
