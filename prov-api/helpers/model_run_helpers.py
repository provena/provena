from prov.model import ProvDocument # type: ignore

def produce_display_name(model_run_id: str) -> str:
    """    produce_display_name
        Given a model run id will produce a display name
        for use in the registry API model run item display 
        name.

        Arguments
        ----------
        model_run_id : str
            The model run handle ID

        Returns
        -------
         : str
            The display name to use in the registry API create 
            request.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # TODO improve display name generation
    return f"Model run id: {model_run_id}"

def produce_serialisation(document : ProvDocument) -> str:
    """    produce_serialisation
        Given a python-prov document, will produce the provenance
        serialisation of that document. This uses python-provs 
        serialisation capabilities. Currently this is json-prov
        but we may want to update the serialisation format later.

        Arguments
        ----------
        document : ProvDocument
            The python prov .ProvDocument

        Returns
        -------
         : str
            The serialised, flat string output

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # TODO determine suitable serialisation for registry storage
    return document.serialize(None, format="json")    
