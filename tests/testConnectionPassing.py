from __future__ import with_statement
from builtins import range
import unittest
import os
import numpy as np
import tempfile
import shutil
import lsst.utils.tests

from lsst.sims.utils.CodeUtilities import sims_clean_up
from lsst.sims.catalogs.db import fileDBObject, CatalogDBObject
from lsst.sims.catalogs.definitions import InstanceCatalog

ROOT = os.path.abspath(os.path.dirname(__file__))


def setup_module(module):
    lsst.utils.tests.init()


class ConnectionPassingTest(unittest.TestCase):
    """
    This will test whether we can can construct InstanceCatalogs
    containing multiple classes of object using only a single
    connection to the database.
    """

    @classmethod
    def write_star_txt(cls):
        np.random.seed(77)
        cls.n_stars = 20
        cls.star_ra = np.random.random_sample(cls.n_stars)*360.0
        cls.star_dec = (np.random.random_sample(cls.n_stars)-0.5)*180.0
        cls.star_umag = np.random.random_sample(cls.n_stars)*10.0 + 15.0
        cls.star_gmag = np.random.random_sample(cls.n_stars)*10.0 + 15.0

        cls.star_txt_name = os.path.join(cls.scratch_dir,
                                         'ConnectionPassingTestStars.txt')

        if os.path.exists(cls.star_txt_name):
            os.unlink(cls.star_txt_name)

        with open(cls.star_txt_name, 'w') as output_file:
            output_file.write("#id raJ2000 decJ2000 umag gmag\n")
            for ix in range(cls.n_stars):
                output_file.write("%d %.4f %.4f %.4f %.4f\n"
                                  % (ix, cls.star_ra[ix], cls.star_dec[ix],
                                     cls.star_umag[ix], cls.star_gmag[ix]))

    @classmethod
    def write_galaxy_txt(cls):
        np.random.seed(88)
        cls.n_galaxies = 100
        cls.gal_ra = np.random.random_sample(cls.n_galaxies)*360.0
        cls.gal_dec = (np.random.random_sample(cls.n_galaxies)-0.5)*180.0
        cls.gal_redshift = np.random.random_sample(cls.n_galaxies)*5.0
        cls.gal_umag = np.random.random_sample(cls.n_galaxies)*10.0+21.0
        cls.gal_gmag = np.random.random_sample(cls.n_galaxies)*10.0+21.0

        cls.gal_txt_name = os.path.join(cls.scratch_dir,
                                        'ConnectionPassingTestGal.txt')

        if os.path.exists(cls.gal_txt_name):
            os.unlink(cls.gal_txt_name)

        with open(cls.gal_txt_name, 'w') as output_file:
            output_file.write("#id raJ2000 decJ2000 redshift umag gmag\n")
            for ix in range(cls.n_galaxies):
                output_file.write("%d %.4f %.4f %.4f %.4f %.4f\n"
                                  % (ix, cls.gal_ra[ix], cls.gal_dec[ix],
                                     cls.gal_redshift[ix],
                                     cls.gal_umag[ix], cls.gal_gmag[ix]))

    @classmethod
    def setUpClass(cls):

        cls.scratch_dir = tempfile.mkdtemp(dir=ROOT, prefix="scratchSpace-")
        cls.write_star_txt()
        cls.write_galaxy_txt()

        cls.dbName = os.path.join(cls.scratch_dir, 'ConnectionPassingTestDB.db')

        if os.path.exists(cls.dbName):
            os.unlink(cls.dbName)

        galDtype = np.dtype([('id', np.int),
                             ('raJ2000', np.float), ('decJ2000', np.float),
                             ('redshift', np.float), ('umag', np.float),
                             ('gmag', np.float)])

        starDtype = np.dtype([('id', np.int), ('raJ2000', np.float),
                              ('decJ2000', np.float), ('umag', np.float),
                              ('gmag', np.float)])

        fileDBObject(cls.star_txt_name,
                     database=cls.dbName, driver='sqlite',
                     runtable='stars', idColKey='id',
                     dtype=starDtype)

        fileDBObject(cls.gal_txt_name,
                     database=cls.dbName, driver='sqlite',
                     runtable='galaxies', idColKey='id',
                     dtype=galDtype)

    @classmethod
    def tearDownClass(cls):
        sims_clean_up()
        if os.path.exists(cls.dbName):
            os.unlink(cls.dbName)

        if os.path.exists(cls.star_txt_name):
            os.unlink(cls.star_txt_name)

        if os.path.exists(cls.gal_txt_name):
            os.unlink(cls.gal_txt_name)

        if os.path.exists(cls.scratch_dir):
            shutil.rmtree(cls.scratch_dir)

    def test_passing(self):
        """
        Test that we can produce a catalog of multiple object types
        drawn from different tables of the same database by passing
        DBConnections
        """

        class starDBObj(CatalogDBObject):
            database = self.dbName
            driver = 'sqlite'
            tableid = 'stars'
            idColKey = 'id'

        class galDBObj(CatalogDBObject):
            database = self.dbName
            driver = 'sqlite'
            tableid = 'galaxies'
            idColKey = 'id'

        class starCatalog(InstanceCatalog):
            column_outputs = ['id', 'raJ2000', 'decJ2000',
                              'gmag', 'umag']

            default_formats = {'f': '%.4f'}

        class galCatalog(InstanceCatalog):
            column_outputs = ['id', 'decJ2000', 'raJ2000',
                              'gmag', 'umag', 'redshift']

            default_formats = {'f': '%.4f'}

        catName = os.path.join(self.scratch_dir,
                               'ConnectionPassingTestOutputCatalog.txt')

        if os.path.exists(catName):
            os.unlink(catName)

        stars = starDBObj()
        galaxies = galDBObj(connection=stars.connection)

        self.assertEqual(stars.connection, galaxies.connection)

        starCat = starCatalog(stars)
        galCat = galCatalog(galaxies)
        starCat.write_catalog(catName, chunk_size=5)
        galCat.write_catalog(catName, write_mode='a', chunk_size=5)

        with open(catName, 'r') as input_file:
            lines = input_file.readlines()
            self.assertEqual(len(lines), self.n_stars+self.n_galaxies+2)
            for ix in range(self.n_stars):
                vals = lines[ix+1].split(',')
                dex = np.int(vals[0])
                self.assertEqual(round(self.star_ra[dex], 4), np.float(vals[1]))
                self.assertEqual(round(self.star_dec[dex], 4), np.float(vals[2]))
                self.assertEqual(round(self.star_gmag[dex], 4), np.float(vals[3]))
                self.assertEqual(round(self.star_umag[dex], 4), np.float(vals[4]))

            offset = 2 + self.n_stars
            for ix in range(self.n_galaxies):
                vals = lines[ix+offset].split(',')
                dex = np.int(vals[0])
                self.assertEqual(round(self.gal_dec[dex], 4), np.float(vals[1]))
                self.assertEqual(round(self.gal_ra[dex], 4), np.float(vals[2]))
                self.assertEqual(round(self.gal_gmag[dex], 4), np.float(vals[3]))
                self.assertEqual(round(self.gal_umag[dex], 4), np.float(vals[4]))
                self.assertEqual(round(self.gal_redshift[dex], 4), np.float(vals[5]))

        if os.path.exists(catName):
            os.unlink(catName)


class MemoryTestClass(lsst.utils.tests.MemoryTestCase):
    pass

if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
