text = "Это пример текста. Этот текст состоит из нескольких слов. Слово, слово, слово."

# Приводим текст к одному регистру и разбиваем его на слова  
words = text.lower().replace('.', '').replace(',', '').split()

# Создаем словарь для подсчета слов  
word_count = {}

# Подсчитываем количество каждого слова  
for word in words:
    if word in word_count:
        word_count[word] += 1  
    else:
        word_count[word] = 1

# Выводим результат  
for word, count in word_count.items():
    print(f"{word}: {count}")
