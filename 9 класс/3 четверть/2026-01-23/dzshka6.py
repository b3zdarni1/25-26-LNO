text = "Это пример текста. Этот текст состоит из нескольких слов. Слово, слово, слово."
words = text.lower().replace('.', '').replace(',', '').split()
word_count = {}
for word in words:
    if word in word_count:
        word_count[word] += 1  
    else:
        word_count[word] = 1
for word, count in word_count.items():
    print(f"{word}: {count}")
