with open("CGrammar.txt", encoding='utf-8') as src:
    with open('CGrammar-with-utf8.txt', 'w', encoding='utf-8') as file:
        file.write(src.read())
        for i in range(2_164_864):
            try:
                if chr(i) != '<' and chr(i) != '>' and chr(i) != '"' and chr(i) != "'" and chr(i) != '|' and chr(i)!="\n":
                    file.write("'" + chr(i) + "'" + "|")
            except UnicodeEncodeError:
                continue
            except ValueError:
                break
