def classFactory(iface):
    from .batch_csv_wkt_importer_US import BatchCSVWKTImporter
    return BatchCSVWKTImporter(iface)
