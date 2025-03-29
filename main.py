from deep_translator import GoogleTranslator

from Translator import Translator

# Use any translator you like, in this example GoogleTranslator
test = Translator()

data = test.translate("გამარჯობა მე ვარ გიორგი, მე და ნინი გავდივართ ჰაკათონზე ტაჩიიი")
print(data)