"""
Model exported as python.
Name : maaki2
Group : 
With QGIS : 32806
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterFileDestination
import processing


class Maaki2(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('corine', 'Corine', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('kiinteistrekisteri', 'Kiinteistörekisteri', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('maannos', 'Maannos', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('maapera', 'Maapera', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Maaki', 'maaki', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Maannosmaapera', 'maannosmaapera', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Maaperamaankaytto', 'maaperamaankaytto', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFileDestination('MaakiCsv', 'maaki csv', fileFilter='GeoPackage (*.gpkg *.GPKG);;ESRI Shapefile (*.shp *.SHP);;(Geo)Arrow (*.arrow *.feather *.arrows *.ipc *.ARROW *.FEATHER *.ARROWS *.IPC);;(Geo)Parquet (*.parquet *.PARQUET);;AutoCAD DXF (*.dxf *.DXF);;Comma Separated Value [CSV] (*.csv *.CSV);;ESRI File Geodatabase (*.gdb *.GDB);;FlatGeobuf (*.fgb *.FGB);;Geoconcept (*.gxt *.txt *.GXT *.TXT);;Geography Markup Language [GML] (*.gml *.GML);;GeoJSON - Newline Delimited (*.geojsonl *.geojsons *.json *.GEOJSONL *.GEOJSONS *.JSON);;GeoJSON (*.geojson *.GEOJSON);;GeoRSS (*.xml *.XML);;GPS eXchange Format [GPX] (*.gpx *.GPX);;INTERLIS 1 (*.itf *.xml *.ili *.ITF *.XML *.ILI);;INTERLIS 2 (*.xtf *.xml *.ili *.XTF *.XML *.ILI);;Keyhole Markup Language [KML] (*.kml *.KML);;Mapinfo TAB (*.tab *.TAB);;Microstation DGN (*.dgn *.DGN);;MS Office Open XML spreadsheet [XLSX] (*.xlsx *.XLSX);;Open Document Spreadsheet [ODS] (*.ods *.ODS);;PostgreSQL SQL dump (*.sql *.SQL);;S-57 Base file (*.000 *.000);;SQLite (*.sqlite *.SQLITE)', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(11, model_feedback)
        results = {}
        outputs = {}

        # Poistetaan turhat muuttujat (maapera)
        alg_params = {
            'COLUMN': ['fid','OBJECTID','PINTAMAALAJI','POHJAMAALAJI','SHAPE_Length','SHAPE_Area'],
            'INPUT': parameters['maapera'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PoistetaanTurhatMuuttujatMaapera'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Poistetaan turhat muuttujat (maannos)
        alg_params = {
            'COLUMN': ['fid','HECTARES','SB_LANDUSE'],
            'INPUT': parameters['maannos'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PoistetaanTurhatMuuttujatMaannos'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Unioni (maannos + maapera)
        # Edellyttää SAGA GIS Provider -lisäosaa. Built in union antaa joissain tapauksissa virheilmoituksen tasojen eroavista geometriatyypeistä, vaikka ne olivat samoja. 
        alg_params = {
            'A': outputs['PoistetaanTurhatMuuttujatMaannos']['OUTPUT'],
            'B': outputs['PoistetaanTurhatMuuttujatMaapera']['OUTPUT'],
            'SPLIT': False,
            'RESULT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['UnioniMaannosMaapera'] = processing.run('saga:union', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Siivotaan unionia
        # Poistetaan unionissa syntyneitä olemattomuuksia, eli vesistöt, joille on määritelty maannos (soil body), maa-alueet, joille ei ole määritelty maannosta sekä alueet, joilla ei ole pintamaalajia lainkaan. 
        alg_params = {
            'EXPRESSION': 'NOT (("SOIL_BODY" IS NOT NULL AND "PINTAMAALA" = 195603) OR ("SOIL_BODY" IS NULL AND "PINTAMAALA" != 195603) OR ("PINTAMAALA" IS NULL))',
            'INPUT': outputs['UnioniMaannosMaapera']['RESULT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SiivotaanUnionia'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Lasketaan pinta-ala
        alg_params = {
            'FIELD_LENGTH': 20,
            'FIELD_NAME': 'AREA',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,  # Decimal (double)
            'FORMULA': '$area',
            'INPUT': outputs['SiivotaanUnionia']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['LasketaanPintaala'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Poistetaan alle neliön alueet
        # Huomattava osa unionin polygoneista oli rajoja, joten poistetaan niistä osa rivien vähentämiseksi. 
        alg_params = {
            'EXPRESSION': 'AREA > 1',
            'INPUT': outputs['LasketaanPintaala']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PoistetaanAlleNelinAlueet'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Fix geometries
        alg_params = {
            'INPUT': outputs['PoistetaanAlleNelinAlueet']['OUTPUT'],
            'METHOD': 1,  # Structure
            'OUTPUT': parameters['Maannosmaapera']
        }
        outputs['FixGeometries'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Maannosmaapera'] = outputs['FixGeometries']['OUTPUT']

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Intersection (corine + maannosmaapera)
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': parameters['corine'],
            'INPUT_FIELDS': ['LEVEL4'],
            'OVERLAY': outputs['FixGeometries']['OUTPUT'],
            'OVERLAY_FIELDS': ['SOIL_BODY','PINTAMAALA'],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': parameters['Maaperamaankaytto']
        }
        outputs['IntersectionCorineMaannosmaapera'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Maaperamaankaytto'] = outputs['IntersectionCorineMaannosmaapera']['OUTPUT']

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Intersection (kiinteisto + maaperamaankaytto)
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': parameters['kiinteistrekisteri'],
            'INPUT_FIELDS': ['kiinteistotunnuksenesitysmuoto'],
            'OVERLAY': outputs['IntersectionCorineMaannosmaapera']['OUTPUT'],
            'OVERLAY_FIELDS': ['LEVEL4','SOIL_BODY','PINTAMAALA'],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['IntersectionKiinteistoMaaperamaankaytto'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Lasketaan ha
        alg_params = {
            'FIELD_LENGTH': 20,
            'FIELD_NAME': 'ha',
            'FIELD_PRECISION': 5,
            'FIELD_TYPE': 0,  # Decimal (double)
            'FORMULA': '$area / 10000',
            'INPUT': outputs['IntersectionKiinteistoMaaperamaankaytto']['OUTPUT'],
            'OUTPUT': parameters['Maaki']
        }
        outputs['LasketaanHa'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Maaki'] = outputs['LasketaanHa']['OUTPUT']

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Save vector features to file
        alg_params = {
            'DATASOURCE_OPTIONS': '',
            'INPUT': outputs['LasketaanHa']['OUTPUT'],
            'LAYER_NAME': '',
            'LAYER_OPTIONS': '',
            'OUTPUT': parameters['MaakiCsv']
        }
        outputs['SaveVectorFeaturesToFile'] = processing.run('native:savefeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['MaakiCsv'] = outputs['SaveVectorFeaturesToFile']['OUTPUT']
        return results

    def name(self):
        return 'maaki2'

    def displayName(self):
        return 'maaki2'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Maaki2()
