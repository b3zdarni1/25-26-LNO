text = "Это пример текста. Этот текст состоит из нескольких слов. Слово, слово, слово."
words = text.lower().replace('.', '').replace(',', '').split()
unique_words = set(words)
unique_word_count = len(unique_words)
print(f"Количество уникальных слов: {unique_word_count}")
