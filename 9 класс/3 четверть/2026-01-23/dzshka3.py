surnames = ["ВАН ДЕР САР", "аршавин", "ЯшИН", "мЕСси", "роналду"]
def popravit_surname(surname):
    return surname.capitalize()  
popravlennii_surnames = [popravit_surname(surname.lower()) for surname in surnames]  
for surname in popravlennii_surnames:
    print(surname)
