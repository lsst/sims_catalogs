"""Instance Catalog"""
import warnings
import numpy as np


class InstanceCatalogMeta(type):
    """Meta class for registering instance catalogs.

    When any new type of instance catalog class is created, this registers it
    in a `registry` class attribute, available to all derived instance
    catalog.
    """
    @staticmethod
    def convert_to_underscores(name):
        """convert, e.g. CatalogName to catalog_name"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def __new__(cls, name, bases, dct):
        # check if attribute catalog_type is specified.
        # If not, create a default
        if 'registry' in dct:
            warnings.warn("registry class attribute should not be "
                          "over-ridden in InstanceCatalog classes. "
                          "Proceed with caution")
        if 'catalog_type' not in dct:
            dct['catalog_type'] = cls.convert_to_underscores(name)
        return super(InstanceCatalogMeta, cls).__new__(cls, name, bases, dct)

    def __init__(cls, name, bases, dct):
        # check if 'registry' is specified.
        # if not, then this is the base class: add the registry
        if not hasattr(cls, 'registry'):
            cls.registry = {}

        # add this class to the registry
        if cls.catalog_type in cls.registry:
            raise ValueError("Catalog Type %s is duplicated"
                             % cls.catalog_type)
        cls.registry[cls.catalog_type] = cls
            
        return super(InstanceCatalogMeta, cls).__init__(name, bases, dct)


class _MimicRecordArray(object):
    """An object used for introspection of the database colums.

    This mimics a numpy record array, but when a column is referenced,
    it logs the reference and returns zeros.
    """
    def __init__(self):
        self.referenced_columns = set()

    def __getitem__(self, column):
        self.referenced_columns.add(column)
        return np.zeros(1)


class InstanceCatalog(object):
    __metaclass__ = InstanceCatalogMeta
    """ Base class for instance catalogs generated by simulations.

    Instance catalogs include a dictionary of numpy arrays which contains 
    core data. Additional arrays can be appended as ancillary data.

    Catalog types and Object types are defined in the CatalogDescription class
    catalogType =  TRIM, SCIENCE, PHOTCAL, DIASOURCE, MISC, INVALID
    objectType = Point, Moving, Sersic, Image, Artefact, MISC
    catalogTable is name of the database table queried
    dataArray dictionary of numpy arrays of data
    """
    # These are the class attributes to be specified in any derived class:
    catalog_type = 'instance_catalog'
    column_outputs = 'all'
    default_formats = {'S':'%s', 'f':'%.4g', 'i':'%i'}
    override_formats = {}
    delimiter = ", "
    endline = "\n"

    # XXX: we need to think about how to best specify metadata
    metadata_outputs = []
    metadata_formats = {}
    
    @classmethod
    def new_catalog(cls, catalog_type, *args, **kwargs):
        """Return a new catalog of the given catalog type"""
        if catalog_type in cls.registry:
            return cls.registry[catalog_type](*args, **kwargs)
        elif issubclass(catalog_type, InstanceCatalog):
            return catalog_type(*args, **kwargs)
        else:
            raise ValueError("Unrecognized catalog_type: %s"
                             % str(catalog_type))

    def __init__(self, db_obj, obs_metadata=None, constraint=None):
        self.db_obj = db_obj
        self._current_chunk = None

        self.obs_metadata = obs_metadata
        self.constraint = constraint
        
        if self.column_outputs == 'all':
            self.column_outputs = self._all_columns()

        self._check_requirements()

    def _all_columns(self):
        """
        Return a list of all available column names, from those provided
        by the instance catalog and those provided by the database
        """
        columns = set(self.db_obj.columnMap.keys())
        getfuncs = [func for func in dir(self) if func.startswith('get_')]
        columns.update([func.strip('get_') for func in getfuncs])
        return list(columns)

    def db_required_columns(self):
        """Get the list of columns required to be in the database object."""
        saved_chunk = self._current_chunk
        self._current_chunk = _MimicRecordArray()

        for column in self.column_outputs:
            col = self.column_by_name(column)

        db_required_columns = list(self._current_chunk.referenced_columns)
        self._current_chunk = saved_chunk

        return db_required_columns

    def column_by_name(self, col_name, *args, **kwargs):
        getfunc = "get_%s" % col_name

        if hasattr(self, getfunc):
            return getattr(self, getfunc)(*args, **kwargs)
        else:
            return self._current_chunk[col_name]

    def _check_requirements(self):
        """Check whether the supplied db_obj has the necessary column names"""
        missing_cols = []

        for col in self.db_required_columns():
            if col not in self.db_obj.columnMap.keys():
                missing_cols.append(col)

        if len(missing_cols) > 0:
            raise ValueError("Required columns missing from database: "
                             "({0})".format(', '.join(missing_cols)))

    def _make_line_template(self, chunk_cols):
        templ_list = []
        for i, col in enumerate(self.column_outputs):
            templ = self.override_formats.get(col, None)

            if templ is None:
                typ = chunk_cols[i].dtype.kind
                templ = self.default_formats.get(typ)

            if templ is None:
                warnings.warn("Using raw formatting for column '%s' "
                              "with type %s" % (col, chunk_cols[i].dtype))
                templ = "%s"
            templ_list.append(templ)

        return self.delimiter.join(templ_list) + self.endline

    def write_catalog(self, filename, chunk_size=None):
        db_required_columns = self.db_required_columns()
        template = None

        file_handle = open(filename, 'w')

        query_result = self.db_obj.query_columns(obs_metadata=self.obs_metadata,
                                                 constraint=self.constraint,
                                                 chunk_size=chunk_size)

        if chunk_size is None:
            query_result = [query_result]

        for chunk in query_result:
            self._current_chunk = chunk
            chunk_cols = [self.column_by_name(col)
                          for col in self.column_outputs]

            # Create the template with the first chunk
            if template is None:
                template = self._make_line_template(chunk_cols)

            # use a generator expression for lines rather than a list
            # for memory efficiency
            file_handle.writelines(template % line
                                   for line in zip(*chunk_cols))
        
        file_handle.close()


#----------------------------------------------------------------------
# Some example uses


class PhotometryMixin(object):
    def get_ug_color(self):
        u = self.column_by_name('umag')
        g = self.column_by_name('gmag')
        return u - g

    def get_gr_color(self):
        g = self.column_by_name('gmag')
        r = self.column_by_name('rmag')
        return g - r


class AstrometryMixin(object):
    def get_ra_corr(self):
        raJ2000 = self.column_by_name('raJ2000')
        return raJ2000 + 0.001  # do something useful here

    def get_dec_corr(self):
        decJ2000 = self.column_by_name('decJ2000')
        return decJ2000 + 0.001  # do something useful here
        

class TrimCatalog(InstanceCatalog, AstrometryMixin, PhotometryMixin):
    catalog_type = 'trim_catalog'
    column_outputs = ['ra_corr', 'dec_corr', 'gmag', 'ug_color']
    default_formats = {'S':'%s', 'f':'%.9g', 'i':'%i'}
    override_formats = {'ra_corr':'%4.2f',
                               'dec_corr':'%6.4f'}

    metadata_outputs = []
    metadata_formats = {}

class TrimCatalogSersic2D(InstanceCatalog, AstrometryMixin, PhotometryMixin):
    catalog_type = 'trim_catalog_SERSIC2D'
    column_outputs = ['objectid','raTrim','decTrim','magNorm','sedFilename',
                      'redshift','shear1','shear2','kappa','raOffset','decOffset',
                      'spatialmodel','majorAxis','minorAxis','positionAngle','sindex',
                      'galacticExtinctionModel','galacticAv','galacticRv',
                      'internalExtinctionModel','internalAv','internalRv']
    default_formats = {'S':'%s', 'f':'%.9g', 'i':'%i'}
    override_formats = {'objectid':'%.2f'}

    metadata_outputs = []
    metadata_formats = {}
    def get_objectid(self):
        return self.column_by_name('galtileid')+self.column_by_name('appendint')
    def get_appendint(self):
        chunkiter = xrange(len(self.column_by_name('galtileid')))
        return np.array([self.db_obj.appendint for i in chunkiter], dtype=float)
    def get_raTrim(self):
        return self.column_by_name('ra_corr')
    def get_decTrim(self):
        return self.column_by_name('dec_corr')
    def get_shear1(self):
        chunklen = len(self.column_by_name('galtileid'))
        return np.zeros(chunklen, dtype=float)
    def get_shear2(self):
        chunklen = len(self.column_by_name('galtileid'))
        return np.zeros(chunklen, dtype=float)
    def get_kappa(self):
        chunklen = len(self.column_by_name('galtileid'))
        return np.zeros(chunklen, dtype=float)
    def get_raOffset(self):
        chunklen = len(self.column_by_name('galtileid'))
        return np.zeros(chunklen, dtype=float)
    def get_decOffset(self):
        chunklen = len(self.column_by_name('galtileid'))
        return np.zeros(chunklen, dtype=float)
    def get_spatialmodel(self):
        chunkiter = xrange(len(self.column_by_name('galtileid')))
        return np.array([self.db_obj.spatialModel for i in
               chunkiter], dtype=(str, 7))
    def get_galacticExtinctionModel(self):
        chunkiter = xrange(len(self.column_by_name('galtileid')))
        return np.array(['CCM' for i in chunkiter], dtype=(str, 3))
    def get_galacticAv(self):
        chunkiter = xrange(len(self.column_by_name('galtileid')))
        #This is a HACK until we get the real values in here
        return np.array([0.1 for i in chunkiter], dtype=float)
    def get_galacticRv(self):
        chunkiter = xrange(len(self.column_by_name('galtileid')))
        return np.array([3.1 for i in chunkiter], dtype=float)


if __name__ == '__main__':
    from lsst.sims.catalogs.generation.db.rewrite import\
        DBObject, ObservationMetaData
    obsMD = DBObject.from_objid('opsim3_61')
    obs_metadata_gal = obsMD.getObservationMetaData(88544919, 0.1, makeCircBounds=True)
    gal_bulge = DBObject.from_objid('galaxyBulge')
                

    star = DBObject.from_objid('msstars')
    obs_metadata = ObservationMetaData(circ_bounds=dict(ra=2.0,
                                                        dec=5.0,
                                                        radius=1.0))

    t = TrimCatalogSersic2D(gal_bulge,
                    obs_metadata=obs_metadata_gal,)
#                    constraint="rmag < 21.")


    print
    print "These are the required columns from the database:"
    print t.db_required_columns()
    print
    print "These are the columns that will be output to the file:"
    print t.column_outputs
    print

    filename = 'catalog_test.dat'
    print "querying and writing catalog to %s:" % filename
    t.write_catalog(filename)
    print " - finished"
