from sqlalchemy import schema
class catalogDbMap (object):
    def __init__(self):
        self.metadataMap = {}
        self.metadataMap['Unrefracted_RA'] = {'opsim3_61':'fieldradeg'}
        self.metadataMap['Unrefracted_Dec'] = {'opsim3_61':'fielddecdeg'}
        self.metadataMap['Opsim_moonra'] = {'opsim3_61':'moonra'}
        self.metadataMap['Opsim_moondec'] = {'opsim3_61':'moondec'}
        self.metadataMap['Opsim_rotskypos'] = {'opsim3_61':'rotskypos'}
        self.metadataMap['Opsim_rottelpos'] = {'opsim3_61':'rottelpos'}
        self.metadataMap['Opsim_filter'] = {'opsim3_61':'filter'}
        self.metadataMap['Opsim_rawseeing'] = {'opsim3_61':'rawseeing'}
        self.metadataMap['Opsim_sunalt'] = {'opsim3_61':'sunalt'}
        self.metadataMap['Opsim_moonalt'] = {'opsim3_61':'moonalt'}
        self.metadataMap['Opsim_dist2moon'] = {'opsim3_61':'dist2moon'}
        self.metadataMap['Opsim_moonphase'] = {'opsim3_61':'moonphase'}
        self.metadataMap['Opsim_obshistid'] = {'opsim3_61':'obshistid'}
        self.metadataMap['Opsim_expmjd'] = {'opsim3_61':'expmjd'}
        self.objectTypes = {}
        self.objectTypes['POINT'] = {}
        self.objectTypes['MOVINGPOINT'] = {}
        self.objectTypes['SERSIC2D'] = {}
        self.objectTypes['STUB'] = {}
        self.objectTypes['POINT']['id'] = {'star':'id'}
        self.objectTypes['POINT']['ra'] = {'star':'ra'}
        self.objectTypes['POINT']['dec'] = {'star':'decl'}
        self.objectTypes['POINT']['glon'] = {'star':'gal_l'}
        self.objectTypes['POINT']['glat'] = {'star':'gal_b'}
        self.objectTypes['POINT']['magNorm'] = {'star':'magNorm'}
        self.objectTypes['POINT']['sedFilename'] = {'star':'sedfilename'}
        self.objectTypes['POINT']['redshift'] = {'star':'vr'}
        self.objectTypes['POINT']['shearXX'] = {'star':0}
        self.objectTypes['POINT']['shearYY'] = {'star':0}
        self.objectTypes['POINT']['magnification'] = {'star':0}
        self.objectTypes['POINT']['properMotionRa'] = {'star':'mudecl'}
        self.objectTypes['POINT']['properMotionDec'] = {'star':'mura'}
        self.objectTypes['POINT']['spatialmodel'] = {'star':'\'Juric\''}
        self.objectTypes['POINT']['galacticExtinctionModel'] = {'star':'\'CCM\''}
        self.objectTypes['POINT']['galacticAv'] = {'star':'ebv*3.1'}
        self.objectTypes['POINT']['galacticRv'] = {'star':3.1}
        self.objectTypes['POINT']['internalExtinctionModel'] = {'star':'\'Amores-Lapine\''}
