from dataclasses import dataclass

@dataclass
class Property:
    title:str
    price:str
    location:str
    area:str
    url:str
    
    def __str__(self) -> str:
        return (f"Title: {self.title}\n"
            f"Location: {self.location}\n"
            f"Price: {self.price}\n"
            f"Area: {self.area}\n"
            f"URL: {self.url}")