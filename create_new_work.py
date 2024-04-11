import json

def add_profession(profession_name, earnings, requirements=None):
    with open("professions.json", "r", encoding="UTF-8") as f:
        data = json.load(f)

    data["professions"][profession_name] = {
        "earnings": earnings,
        "requirements": requirements or {}
    }

    with open("professions.json", "w", encoding="UTF-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def main():
    profession_name = input("Введите название профессии: ")
    earnings = input("Введите доход профессии (в формате '150-250'): ")
    items = input("Введите необходимые предметы через запятую (если есть): ").split(", ")
    money = input("Введите необходимую сумму денег (если есть): ")
    ethereum = input("Введите необходимое количество ethereum (если есть): ")

    requirements = {}
    if items:
        requirements["items"] = items
    if money:
        requirements["money"] = int(money)
    if ethereum:
        requirements["ethereum"] = int(ethereum)

    add_profession(profession_name, earnings, requirements)

if __name__ == "__main__":
    main()