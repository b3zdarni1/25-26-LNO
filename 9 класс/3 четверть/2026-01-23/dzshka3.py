def count_glasnie_and_soglasnie(text):
    glasnie = "аеёиоуыэюяАЕЁИОУЫЭЮЯаeiouyAEIOUY"
    soglasnie = "бвгджзйклмнпрстфхцчшщБВГДЖЗЙКЛМНПРСТФХЦЧШЩ" 
    glasnie_count = 0  
    soglasnie_count = 0  
    for char in text: 
        if char in glasnie:
            glasnie_count += 1  
        elif char in soglasnie:
            soglasnie_count += 1
    return glasnie_count, soglasnie_count
  
input_text = "Привет, как дела?"
glasnie, soglasnie = count_glasnie_and_soglasnie(input_text)

print(glasnie, soglasnie)
