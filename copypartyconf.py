import yaml

async def construct_string_from_accounts(group: str, accounts: list):
    sections = {"accounts": {}, "groups": {}}
    for account in accounts:
        sections["accounts"] |= {account.username: account.password}
    sections["groups"] = {group: [a.username for a in accounts]}
    return await to_string(sections)

async def parse(string: str) -> dict:
    sections = {}
    nextSection = 0
    while nextSection != -1:
        beginSection = string.find("]")
        nextSection = string[beginSection+2:].find("[")
        if not nextSection == -1:
            section = string[:beginSection+nextSection+1][beginSection+2:]
        else:
            section = string[beginSection+2:][:-1]
        splittedSection = section.splitlines()
        sections[string[:beginSection][1:]] = {}
        for semiSection in splittedSection:
            clean = semiSection.strip()
            content = yaml.safe_load(clean)
            if content:
                subContent = list(content.values())[0]
                if "," in subContent:
                    subContent = [item.strip() for item in subContent.split(',')]
                sections[string[:beginSection][1:]] |= {list(content.keys())[0]: subContent}
        string = string[beginSection+2+nextSection:]
    return sections

async def to_string(sections: dict):
    constructString = ""
    for key in sections.keys():
        constructString += f"[{key}]\n"
        subSection = sections[key]
        for item in subSection.items():
            subString = item[1]
            if type(subString) is list:
                subString = ', '.join(subString)
            constructString += f"  {item[0]}: {subString}\n"
    return constructString[:-1]