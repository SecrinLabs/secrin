from abc import ABC, abstractmethod

class BaseStore(ABC):
    @abstractmethod
    def getEmbedder(self):
        pass

    @abstractmethod
    def getLlm(self):
        pass