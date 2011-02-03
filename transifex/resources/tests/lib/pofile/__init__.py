import os
import unittest
from transifex.txcommon.tests.base import BaseTestCase
from transifex.languages.models import Language
from transifex.resources.models import *
from transifex.resources.formats.pofile import POHandler

from transifex.addons.suggestions.models import Suggestion

class POFile(BaseTestCase):
    """Suite of tests for the pofile lib."""
    def test_pot_parser(self):
        """POT file tests."""
        # Parsing POT file
        handler = POHandler('%s/tests.pot' % 
            os.path.split(__file__)[0])

        handler.set_language(self.resource.source_language)
        handler.parse_file()
        self.stringset = handler.stringset
        entities = 0

        # POT has no associated language
        self.assertEqual(self.stringset.target_language, None)

        for s in self.stringset.strings:
            # Testing if source entity and translation are the same
            if not s.pluralized:
                self.assertEqual(s.source_entity, s.translation)

            # Testing plural number
            if s.source_entity == '{0} results':
                self.assertEqual(s.rule, 5)

            # Counting number of entities
            if s.rule == 5:
                entities += 1

        # Asserting number of entities - POT file has 3 entries.
        self.assertEqual(entities, 3)

    def test_po_parser_pt_BR(self):
        """Tests for pt_BR PO file."""
        handler = POHandler('%s/pt_BR.po' % 
            os.path.split(__file__)[0])


        handler.set_language(self.language)
        handler.parse_file()
        self.stringset = handler.stringset

        nplurals = 0

        for s in self.stringset.strings:

            # Testing plural number
            if s.source_entity == '{0} results':
                self.assertEqual(s.rule, 5)

            if s.source_entity == '{0} result' and s.pluralized:
                nplurals += 1

        # Asserting nplurals based on the number of plurals of the 
        # '{0 results}' entity - pt_BR has nplurals=2
        self.assertEqual(nplurals, 2)

    def test_po_parser_ar(self):
        """Tests for ar PO file."""
        handler = POHandler('%s/ar.po' % 
            os.path.split(__file__)[0])

        handler.set_language(self.language_ar)
        handler.parse_file()
        self.stringset = handler.stringset
        nplurals = 0

        for s in self.stringset.strings:

            # Testing if source entity and translation are NOT the same
            self.assertNotEqual(s.source_entity, s.translation)

            # Testing plural number
            if s.source_entity == '{0} results':
                self.assertEqual(s.rule, 5)

            if s.source_entity == '{0} result' and s.pluralized:
                nplurals += 1

        # Asserting nplurals based on the number of plurals of the 
        # '{0 results}' entity - ar has nplurals=6.
        self.assertEqual(nplurals, 6)

    def test_po_save2db(self):
        """Test creating source strings from a PO/POT file works"""
        handler = POHandler('%s/tests.pot' % 
            os.path.split(__file__)[0]) 

        l = Language.objects.get(code='en_US')

        handler.set_language(l)
        handler.parse_file(is_source=True)

        r = self.resource

        handler.bind_resource(r)

        handler.save2db(is_source=True)

        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 3)

        self.assertEqual( len(Translation.objects.filter(source_entity__resource=r,
            language=l)), 4)

        handler.bind_file('%s/ar.po' % os.path.split(__file__)[0])
        l = Language.objects.by_code_or_alias('ar')
        handler.set_language(l)
        handler.parse_file()

        handler.save2db()

        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 3)

        self.assertEqual( len(Translation.objects.filter(source_entity__resource=r,
            language=l)), 8)

        r.delete()

    def test_logical_ids(self):
        """Test po files with logical ids instead of normal strings"""


        # Empty our resource
        SourceEntity.objects.filter(resource=self.resource).delete()

        # Make sure that we have no suggestions to begin with
        self.assertEqual(Suggestion.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 0)

        # Import file with two senteces
        handler = POHandler('%s/logical_ids/tests.pot' %
            os.path.split(__file__)[0])
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)

        # import pt_BR translation
        handler = POHandler('%s/logical_ids/pt_BR.po' %
            os.path.split(__file__)[0])
        handler.bind_resource(self.resource)
        handler.set_language(self.language)
        handler.parse_file()
        handler.save2db()

        # Make sure that we have all translations in the db
        self.assertEqual(Translation.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 2)

        source = SourceEntity.objects.get(resource=self.resource)
        en_trans = Translation.objects.get(source_entity__resource=self.resource,
            language = self.resource.source_language)
        pt_trans = Translation.objects.get(source_entity__resource=self.resource,
            language = self.language)

        import ipdb; ipdb.set_trace()
        # Check to see that the correct strings appear as the translations and
        # not the logical id
        self.assertEqual(en_trans.string, "Hello, World!")
        self.assertEqual(pt_trans.string, "Holas, Amigos!")
        self.assertEqual(source.string, "source_1")

    def test_convert_to_suggestions(self):
        """Test convert to suggestions when importing new source files"""

        # Empty our resource
        SourceEntity.objects.filter(resource=self.resource).delete()

        # Make sure that we have no suggestions to begin with
        self.assertEqual(Suggestion.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 0)

        # Import file with two senteces
        handler = POHandler('%s/suggestions/tests.pot' %
            os.path.split(__file__)[0])
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)

        # import pt_BR translation
        handler = POHandler('%s/suggestions/pt_BR.po' %
            os.path.split(__file__)[0])
        handler.bind_resource(self.resource)
        handler.set_language(self.language)
        handler.parse_file()
        handler.save2db()

        # Make sure that we have all translations in the db
        self.assertEqual(Translation.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 4)

        # import source with small modifications
        handler = POHandler('%s/suggestions/tests-diff.pot' %
            os.path.split(__file__)[0])
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)

        # Make sure that all suggestions were added
        self.assertEqual(Suggestion.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 1)

        # Make both strings are now untranslated
        self.assertEqual(Translation.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 2)
