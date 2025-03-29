import typing
from deep_translator import GoogleTranslator
from googletrans.models import Translated


# translate georgian text to english

class Translator:
    def __init__(self, source='auto', target='en'):
        self.source = source
        self.target = target

    # translater
    def translate(self, text:typing.Union[str, typing.List[str]]) -> typing.List[Translated]:
        return GoogleTranslator(source=self.source, target=self.target).translate(text)
