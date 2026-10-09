from rrule import rrule, build_rruleset
from rrule.rrule import RRuleSet, __all__, __spec__, __loader__, build_rruleset


class rrulewrapper:
    def __init__(self, freq, **kwargs):
        self._construct = kwargs.copy()
        self._construct["freq"] = freq
        # self._rrule = rrule(**self._construct)
        self._rrule = build_rruleset(**self._construct)  # TODO : Vérifier l'utilisation de rrule !

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        return getattr(self._rrule, name)
    
    def set(self, **kwargs):
        self._construct.update(kwargs)
        # self._rrule = rrule(**self._construct)
        self._rrule = RRuleSet(**self._construct)  # TODO : Vérifier l'utilisation de rrule !
