from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.http import JsonResponse
from django.conf import settings
import requests
import json 
import ast, re
import psycopg2
from .models import DocSource, SnippetCode, GeonetworkMetadata

ACCEPT_HTTP = "application/json"
CONTENT_TYPE = "application/json"
GEONETWORK_BASE_URL = settings.GEONETWORK_BASE_URL
EDP_DISCOVERY_URL = settings.EDP_DISCOVERY_URL
DOI_URL = settings.DOI_URL
OPENEO_URL = settings.OPENEO_URL
DATA_CITE_API = settings.DATA_CITE_API
GEONETWORK_URL = settings.GEONETWORK_URL


def _get_db_connection():
    db = settings.DATABASES["default"]
    return psycopg2.connect(
        database=db["NAME"],
        user=db["USER"],
        password=db["PASSWORD"],
        host=db["HOST"],
        port=db["PORT"],
    )

class DocsPageView(generic.ListView):
    template_name = 'docs.html'
    context_object_name = 'latest_docs_sources_list'

    def get_queryset(self):
        """Return the docs sources."""
        return DocSource.objects.all().order_by('-pub_date')
    #model = DocSource
    #return render(request, 'docs.html', {})

def main_page(request):
    return render(request, 'main_page.html', {})
    #return render(request, 'maintenance.html', {})

def discovery(request):
    title_list = "no title found"
    #category_list = "no category found"
    category_list = ["no category found"]
    try:
        #print(request.GET)
        conn = _get_db_connection()
        cursor = conn.cursor()
        tmp_category_list = GeonetworkMetadata.objects.values_list('category', flat=True)
        category_list = []
        for c in tmp_category_list:
            if c not in category_list and c != None:
                category_list.append(c)
        
        title_list = ""

        where_clause_array = []
        where_clause_array.append("all")
        if request.GET.get('categories'):
            cateogories_selected = request.GET.get('categories')
            if "all" not in cateogories_selected:
                #print("CATEGORIES " + cateogories_selected)                
                #print(cateogories_selected.split(","))
                where_clause_array.remove("all")
                for c in cateogories_selected.split(","):
                    where_clause_array.append("category='"+c+"'")
            else:
                where_clause_array.append("all")
        
        #if 'term' in request.GET:  
        #print(request.GET.get("term"))
        #searchKeyword = request.GET.get("term")
        #category_query = "SELECT DISTINCT(category) FROM main_page_geonetworkmetadata mpg WHERE category ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%'"
        category_query = "SELECT DISTINCT(category) FROM main_page_geonetworkmetadata mpg"
        cursor.execute(category_query)
        results = cursor.fetchall()
        for i in results:
            if i[0]:
                #title_list.append(i[0].replace("\"","")) 
                title_list = title_list + "," +i[0]
        #keyword_query = "SELECT DISTINCT(keyword) FROM main_page_geonetworkmetadata mpg WHERE keyword ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%'"
        keyword_query = "SELECT DISTINCT(keyword) FROM main_page_geonetworkmetadata mpg"
        cursor.execute(keyword_query)
        results = cursor.fetchall()
        for i in results:
            if i[0]:
                #title_list.append(i[0].replace("\"","")) 
                keyword_list = i[0].split(",")
                for keyword in keyword_list:
                    if keyword not in title_list: 
                        title_list = title_list + "," + keyword
        #print(title_list)
        #title_query = "SELECT title FROM main_page_geonetworkmetadata mpg WHERE title ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%'"
        title_query = "SELECT title FROM main_page_geonetworkmetadata mpg"
        cursor.execute(title_query)
        results = cursor.fetchall()
        for i in results:
            if i[0]:
                #title_list.append(i[0].replace("\"","")) 
                title_list = title_list + "," +i[0]
        #print(len(title_list))
        #if (len(title_list) == 0):
        if (title_list == ""):
            title_list = "no title found"    
        #    return JsonResponse(title_list, safe=False, status=200)
        if request.GET.get('period_begin') and request.GET.get('period_end') and request.GET.get('box') and request.GET.get('search'):
            period_begin = request.GET.get('period_begin')
            period_end = request.GET.get('period_end')
            #print(period_begin + " " + period_end)
            searchKeyword = request.GET.get('search')
            boundingbox = request.GET.get('box')
            boundingbox = boundingbox.split(",")
            #print(boundingbox)
            polygon = ""
            for i in range(len(boundingbox)):
                if i == 0:
                    polygon = polygon + boundingbox[i]
                else:
                    if i % 2 == 0:
                        polygon = polygon + "," + boundingbox[i]
                    elif i%2 != 0:
                        polygon = polygon + " " + boundingbox[i]
            
            polygon = "POLYGON((" + polygon + "))"

            if "all" not in where_clause_array:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
            else:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' ORDER BY title ASC"

            #final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, period_begin, period_end FROM main_page_geonetworkmetadata WHERE date_trunc('day', period_begin) >= '"+period_begin+"' AND date_trunc('day', period_end) <= '"+period_end+"' ORDER BY title ASC;"
            print(final_query)
            cursor.execute(final_query)
            results = cursor.fetchall()
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        if request.GET.get('period_begin') and request.GET.get('period_end') and request.GET.get('box'):
            period_begin = request.GET.get('period_begin')
            period_end = request.GET.get('period_end')
            #print(period_begin + " " + period_end)
            boundingbox = request.GET.get('box')
            boundingbox = boundingbox.split(",")
            #print(boundingbox)
            polygon = ""
            for i in range(len(boundingbox)):
                if i == 0:
                    polygon = polygon + boundingbox[i]
                else:
                    if i % 2 == 0:
                        polygon = polygon + "," + boundingbox[i]
                    elif i%2 != 0:
                        polygon = polygon + " " + boundingbox[i]
            #print(polygon)
            polygon = "POLYGON((" + polygon + "))"   

            if "all" not in where_clause_array:         
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
            else:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' ORDER BY title ASC"
            #final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, period_begin, period_end FROM main_page_geonetworkmetadata WHERE date_trunc('day', period_begin) >= '"+period_begin+"' AND date_trunc('day', period_end) <= '"+period_end+"' ORDER BY title ASC;"
            print(final_query)
            cursor.execute(final_query)
            results = cursor.fetchall()
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        if request.GET.get('period_begin') and request.GET.get('period_end') and request.GET.get('search'):
            period_begin = request.GET.get('period_begin')
            period_end = request.GET.get('period_end')
            #print(period_begin + " " + period_end)
            searchKeyword = request.GET.get('search')
            #print("KEYWORD " + searchKeyword)
            if "all" not in where_clause_array:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
            else:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' ORDER BY title ASC"

            #final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, period_begin, period_end FROM main_page_geonetworkmetadata WHERE date_trunc('day', period_begin) >= '"+period_begin+"' AND date_trunc('day', period_end) <= '"+period_end+"' ORDER BY title ASC;"
            print(final_query)
            cursor.execute(final_query)
            results = cursor.fetchall()
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        if request.GET.get('box') and request.GET.get('search'):
            searchKeyword = request.GET.get('search')
            boundingbox = request.GET.get('box')
            boundingbox = boundingbox.split(",")
            #print(boundingbox)
            polygon = ""
            for i in range(len(boundingbox)):
                if i == 0:
                    polygon = polygon + boundingbox[i]
                else:
                    if i % 2 == 0:
                        polygon = polygon + "," + boundingbox[i]
                    elif i%2 != 0:
                        polygon = polygon + " " + boundingbox[i]
            
            polygon = "POLYGON((" + polygon + "))"  
            #print(polygon)
            #print("KEYWORD " + searchKeyword + " BBOX " + boundingbox)
            if "all" not in where_clause_array:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
            else:            
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' ORDER BY title ASC"
            print(final_query)
            cursor.execute(final_query)
            results = cursor.fetchall()
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        if request.GET.get('period_begin') and request.GET.get('period_end'):
            period_begin = request.GET.get('period_begin')
            period_end = request.GET.get('period_end')
            #print(period_begin + " " + period_end)
            if "all" not in where_clause_array:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, period_begin, period_end FROM main_page_geonetworkmetadata WHERE (date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"') AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC;"
            else:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, period_begin, period_end FROM main_page_geonetworkmetadata WHERE date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' ORDER BY title ASC;"
            print(final_query)
            cursor.execute(final_query)
            results = cursor.fetchall()
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)

        if request.GET.get('box'):
            print("BOX")            
            boundingbox = request.GET.get('box')
            boundingbox = boundingbox.split(",")
            #print(boundingbox)
            polygon = ""
            for i in range(len(boundingbox)):
                if i == 0:
                    polygon = polygon + boundingbox[i]
                else:
                    if i % 2 == 0:
                        polygon = polygon + "," + boundingbox[i]
                    elif i%2 != 0:
                        polygon = polygon + " " + boundingbox[i]
            #print(polygon)
            polygon = "POLYGON((" + polygon + "))"

            if "all" not in where_clause_array:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
            else:            
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) ORDER BY title ASC"
            print(final_query)
            cursor.execute(final_query)
            #print(conn.commit())
            results = cursor.fetchall()
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        if request.GET.get('search'):
            print("SEARCH")
            searchKeyword = request.GET.get('search')
            
            if request.GET.get('json') == "no":
                if "all" not in where_clause_array:
                    final_query = "SELECT uuid FROM main_page_geonetworkmetadata mpg WHERE (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
                else:
                    final_query = "SELECT uuid FROM main_page_geonetworkmetadata mpg WHERE (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' ORDER BY title ASC"

                cursor.execute(final_query)
                #print(final_query)
                results = cursor.fetchall()            
                #print(uuids_list)
                uuids_list = []
                for r in results:
                    uuids_list.append(r[0])
                metadata_results = GeonetworkMetadata.objects.filter(uuid__in=uuids_list)
                return render(request, 'discovery.html', {'metadata_results': metadata_results, 'title_list': title_list, 'category_list': category_list})
            else:
                if "all" not in where_clause_array:
                    final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
                else:
                    final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' ORDER BY title ASC"
                cursor.execute(final_query)
                #print(final_query)
                results = cursor.fetchall() 
                return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
            
        if request.GET.get('categories'):
            print("CATEGORY")
            cateogories_selected = request.GET.get('categories')
            if "all" not in cateogories_selected:
                #print("CATEGORIES " + cateogories_selected)
                where_clause_array = []
                #print(cateogories_selected.split(","))
                for c in cateogories_selected.split(","):
                    where_clause_array.append("category='"+c+"'")

                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE " + " OR ".join(where_clause_array) + " ORDER BY title ASC"
            else:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg ORDER BY title ASC"
            print(final_query)
            cursor.execute(final_query)
            results = cursor.fetchall()
            #print(results)
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)

    except GeonetworkMetadata.DoesNotExist:
        raise Http404("GeonetworkMetadata does not exist")
    
    cursor.close()
    conn.close()
    metadata_results = GeonetworkMetadata.objects.order_by('title')
    #print(title_list)    
    #print(type(metadata_results))
    return render(request, 'discovery.html', {'metadata_results': metadata_results, 'title_list': title_list, 'category_list': category_list})
    #return render(request, 'discovery.html', {}) 
    
def jupyter_page(request):
    return render(request, 'jupyter.html', {})

def openeo_page(request):
    return render(request, 'openeo.html', {})

def pgadmin_page(request):
    return render(request, 'pgadmin.html', {})

def maps_page(request):
    return render(request, 'maps.html', {})

def terms_conditions_page(request):
    return render(request, 'terms_conditions.html', {})

def CheckDataciteURL(url):
    print("")
    try:
        #print(url)
        response = requests.head(url)
        #print("CheckDataciteURL "+response)
        return response.status_code == 200
    except requests.RequestException:
        print(requests.RequestException)
        return False

def CheckDOIURL(url):
    try:
        #print(url)
        response = requests.head(url)
        #print("CheckDOIURL "+response)
        return response.status_code == 200
    except requests.RequestException:
        print(requests.RequestException)
        return False

def result_detail(request, uuid):
    #uuid = "51f8f326-7964-11ee-9a8e-47abc4958022"
    metadata_details = get_metadata_details(request, uuid)
    #print(metadata_details)
    creators, rights, type, publisher = get_info_publication_complete(uuid)
    #print(creators)
    #print(type)

    metadata_details['creators'] = creators
    metadata_details['rights'] = rights
    name_collection = ""
    if 'name_collection' in metadata_details:
        name_collection = metadata_details['name_collection']
    if ("error"  not in metadata_details):
        snippet_code_list = SnippetCode.objects.filter(snippet_category__icontains=metadata_details["category"])
        for i in snippet_code_list:
            if 'name_collection' in metadata_details:
                i.snippet_code = i.snippet_code.replace("NAME_COLLECTION", metadata_details['name_collection'])
            if 'minLon' in metadata_details:
                i.snippet_code = i.snippet_code.replace("MIN_LON", str(metadata_details['minLon']))
            if 'minLat' in metadata_details:
                i.snippet_code = i.snippet_code.replace("MIN_LAT", str(metadata_details['minLat']))
            if 'maxLon' in metadata_details:
                i.snippet_code = i.snippet_code.replace("MAX_LON", str(metadata_details['maxLon']))
            if 'maxLat' in metadata_details:
                i.snippet_code = i.snippet_code.replace("MAX_LAT", str(metadata_details['maxLat']))
            if 'tempExtentBegin' in metadata_details and 'tempExtentEnd' in metadata_details:
                i.snippet_code = i.snippet_code.replace("TEMPORAL_EXTENT", "["+metadata_details['tempExtentBegin']+","+metadata_details['tempExtentEnd']+"]")
                i.snippet_code = i.snippet_code.replace("STARTTIME", metadata_details['tempExtentBegin'])
                i.snippet_code = i.snippet_code.replace("ENDTIME", metadata_details['tempExtentEnd'])
            if 'title' in metadata_details:
                if metadata_details['category'].lower() == 'sos':
                    title_split = metadata_details['title'].split('_')
                    foi = title_split[1]
                    observable_property = title_split[0]
                    procedure = metadata_details['title']
                    sos_url = 'http://monalisasos.eurac.edu/sos/api/v1/'
                    i.snippet_code = i.snippet_code.replace('FOI', '\"'+foi+'\"')
                    i.snippet_code = i.snippet_code.replace('OBSERVABLE_PROPERTY', '\"'+observable_property+'\"')
                    i.snippet_code = i.snippet_code.replace('PROCEDURE', '\"'+procedure+'\"')
                    i.snippet_code = i.snippet_code.replace('SOS_URL', '\"'+sos_url+'\"')

        docs_list = DocSource.objects.filter(source_category__icontains=metadata_details["category"])

        url_repository = ""

        context = {
            "uuid" : uuid,
            "publisher" : publisher,
            "type" : type,
            "name_collection": name_collection,
            #"result_json" : result_json["metadata"],
            "result_json" : metadata_details,
            "snippet_code_list" : snippet_code_list,
            "docs_list" : docs_list,
            "url_repository": url_repository
            #'title': result_json["metadata"]["title"],
        }
        response = render(request, 'result_detail.html', context)
        #Signposting HTTP HEAD Link <https://example.org/linkset/7507/lset> ; rel="linkset" ; type="application/linkset" , 
        response['Link'] = '<' + EDP_DISCOVERY_URL + "linkset/" + uuid + '> ; rel="linkset" ; type="application/linkset+json"' + ", " + '<' + EDP_DISCOVERY_URL + "jsonld/" + uuid + '> ; rel="describedby" ; type="application/ld+json"'
        #response['Link'] = '<' + EDP_DISCOVERY_URL + "jsonld/" + uuid + '> ; rel="ld" ; type="application/ld+json"'
        
        return response
    else:
        #print(metadata_details)
        context = {
            "error" : "No metadata found for this uuid (" + uuid + ")"
        }

        return render(request, 'result_detail.html', context)

def get_metadata_details(request, uuid):
    #try:
        metadata_detail = {}
        #url = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&_draft=y+or+n+or+e&_isTemplate=y+or+n&fast=index&uuid="+uuid
        url = GEONETWORK_BASE_URL + "/srv/api/search/records/_search"
        #print(url)
        body = "{\"query\":{\"bool\":{\"must\":[{\"multi_match\":{\"query\":\""+uuid+"\",\"fields\":[\"id\",\"uuid\"]}},{\"terms\":{\"isTemplate\":[\"n\",\"y\"]}},{\"terms\":{\"draft\":[\"n\",\"y\",\"e\"]}}]}}}"
        headers = {'ACCEPT': ACCEPT_HTTP, 'CONTENT-TYPE': CONTENT_TYPE}
        results = requests.post(url, data=body, headers=headers)
        tmp = json.loads(results.text)
        #print(tmp)
        metadataRecords = tmp['hits']['hits'][0]['_source']
        #print(metadataRecords)

        if 'contact' in metadataRecords:
            for contact in metadataRecords['contact']:
                if 'pointOfContact' in contact['role']:
                    metadata_detail['contactMetadata'] = { 'contactName' : contact['organisationObject']['default'], 'email' : contact['email'], 'address' : contact['address'] }
                if 'author' in contact['role']:
                    metadata_detail['contactResource'] = { 'contactName' : contact['organisationObject']['default'], 'email' : contact['email'], 'address': contact['address'] }

        if 'MD_LegalConstraintsOtherConstraintsObject' in metadataRecords:
            metadata_detail['legalConstraints'] = metadataRecords['MD_LegalConstraintsOtherConstraintsObject'][0]['default']
        if 'MD_LegalConstraintsUseLimitationObject' in metadataRecords:
            metadata_detail['legalConstraints'] = metadataRecords['MD_LegalConstraintsUseLimitationObject'][0]['default']

        
        if 'crsDetails' in metadataRecords:
            metadata_detail['crs'] = metadataRecords['crsDetails'][0]['name'] + " ("+metadataRecords['crsDetails'][0]['code']+":"+metadataRecords['crsDetails'][0]['codeSpace']+")"

        if 'cl_spatialRepresentationType' in metadataRecords:
            metadata_detail['refSys'] = metadataRecords['cl_spatialRepresentationType'][0]['default']

        if 'geom' in metadataRecords:
            k=0
            for i in metadataRecords['geom']['coordinates'][0]:
                if k == 0:
                    minLat = i[1]
                    minLon = i[0]
                    maxLat = i[1]
                    maxLon = i[0]
                if minLat > i[1]:
                    minLat = i[1]
                if minLon > i[0]:
                    minLon = i[0]
                if maxLat < i[1]:
                    maxLat = i[1]
                if maxLon < i[0]:
                    maxLon = i[0]
                k=k+1        
            metadata_detail['minLat'] = minLat
            metadata_detail['minLon'] = minLon
            metadata_detail['maxLat'] = maxLat
            metadata_detail['maxLon'] = maxLon

        if 'resourceTitleObject' in metadataRecords:
            metadata_detail['title'] = metadataRecords['resourceTitleObject']['default']
        elif 'resourceAltTitleObject' in metadataRecords:
            metadata_detail['title'] = metadataRecords['resourceAltTitleObject']['default']
        if 'resourceAbstractObject' in metadataRecords:
            metadata_detail['abstract'] = metadataRecords['resourceAbstractObject']['default']

        if 'resourceIdentifier' in metadataRecords: 
            
            if "http" in metadataRecords['resourceIdentifier'][0]['codeSpace']:
                #print("get openeo URL repository "+metadataRecords['resourceIdentifier'][0]['codeSpace'])
                if "https://openeo.eurac.edu/collections" in metadataRecords['resourceIdentifier'][0]['codeSpace']:
                    metadata_detail['url_repository'] = metadataRecords['resourceIdentifier'][0]['codeSpace']
                try:
                    swhid_link = json.loads(requests.get(metadataRecords['resourceIdentifier'][0]['codeSpace']).text)
                #print(swhid_link['links'])
                    for e in swhid_link['links']:
                        if e['title'] == "SWHID":
                            metadata_detail['swhid'] = e['href']
                except:
                    print("swhid_link is not a json")
                

        if 'overview' in metadataRecords:
            metadata_detail['thumbnail'] = metadataRecords['overview'][0]['url']

        gn_cat = GeonetworkMetadata.objects.filter(uuid=uuid)
        #print(gn_cat)
        if gn_cat:
            if gn_cat[0].category:
                metadata_detail['category'] = gn_cat[0].category
            if gn_cat[0].doi:                    
                print(gn_cat[0].doi)
                if CheckDOIURL(gn_cat[0].doi) or CheckDataciteURL(DATA_CITE_API+uuid):
                    metadata_detail['doi'] = gn_cat[0].doi
                else:
                    print("url invalid, no doi")
            if gn_cat[0].citation:
                metadata_detail['citation'] = gn_cat[0].citation
            if gn_cat[0].supplemental_information:
                metadata_detail['supplemental_information'] = gn_cat[0].supplemental_information
            if gn_cat[0].presentation_form:
                metadata_detail['presentationForm'] = gn_cat[0].presentation_form
            #print(gn_cat[0].cl_topic)
            if gn_cat[0].cl_topic:
                metadata_detail['cl_topic'] = gn_cat[0].cl_topic

        
        if 'tag' in metadataRecords:
            keywords = []
            for t in metadataRecords['tag']:        
                keywords.append(t['default'])   
            metadata_detail['keyword'] = ", ".join(keywords)

        if 'lineage' in metadataRecords:
            metadata_detail['lineage'] = metadataRecords['lineageObject']

        # period_begin = ""
        # period_end = ""
        if 'resourceTemporalExtentDetails' in metadataRecords:
            if 'date' in metadataRecords['resourceTemporalExtentDetails'][0]['start']:
                metadata_detail['tempExtentBegin'] = metadataRecords['resourceTemporalExtentDetails'][0]['start']['date']
            if 'date' in metadataRecords['resourceTemporalExtentDetails'][0]['end']:    
                metadata_detail['tempExtentEnd'] = metadataRecords['resourceTemporalExtentDetails'][0]['end']['date']

        if 'link' in metadataRecords:
            #print(metadataRecords['link'][0])            
            if 'nameObject' in metadataRecords['link'][0]:
                metadata_detail['name_collection'] = metadataRecords['link'][0]['nameObject']['default']
            # if 'urlObject' in metadataRecords['link'][0]:
            #     metadata_detail['url_object'] = metadataRecords['link'][0]['urlObject']['default']

        caption_category = gn_cat[0].category
        #print(caption_category)
        if 'linkUrlProtocolWWWDOWNLOAD10httpdownload' in metadataRecords:
            url_objects = []
            #print(metadataRecords['linkUrlProtocolWWWDOWNLOAD10httpdownload'])
            if type(metadataRecords['linkUrlProtocolWWWDOWNLOAD10httpdownload']) is list:
                #print(len(metadataRecords['linkUrlProtocolWWWDOWNLOAD10httpdownload']))
                for l in metadataRecords['linkUrlProtocolWWWDOWNLOAD10httpdownload']:
                    link_splitted = l.split("&")
                    #print(link_splitted)
                    if "https://maps.eurac.edu/download/" in l:
                        #print(l)    
                        id_collection = l.split("/")[-1]
                        if id_collection:                                        
                            metadata_detail['url_repository'] = "https://maps.eurac.edu/catalogue/#/dataset/"+id_collection
                        #print("https://maps.eurac.edu/catalogue/#/dataset/"+id_collection)
                    if 'outputFormat' in l or 'format' in l:
                        for e in link_splitted:       
                            if 'outputFormat' in e:                     
                                #print(e)
                                if caption_category == "Maps":
                                    if "https://maps.eurac.edu/" in l:
                                        if "https://maps.eurac.edu/uploaded/thumbs" in l:
                                            print("Do nothing")
                                        if "https://maps.eurac.edu/download/" in l:
                                            #print("Do nothing")    
                                            id_collection = l.split("/")[-1]                                        
                                            metadata_detail['url_repository'] = "https://maps.eurac.edu/catalogue/#/dataset/"+id_collection
                                        else:
                                            #print(l)
                                            tmp = l.replace("https://maps.eurac.edu/", "").split("?")
                                            #print(tmp)
                                            for k in tmp[1].split('&'):
                                                #tmpk = k.split("&")
                                                if "outputFormat" in k:
                                                    url_objects.append(dict(l=l,file_type=k.replace("outputFormat=", "").replace("%2F", " ")
                                                                            .replace("%3A", " ")
                                                                            .replace("%3B", " ")
                                                                            .replace("%3D", " ")))
                                                    #print(k)
                                else:
                                    url_objects.append(dict(l=l,file_type=e[13:]))
                            if 'format_options' in e:
                                if caption_category == "Maps":
                                    if "https://maps.eurac.edu/" in l:
                                        if "https://maps.eurac.edu/uploaded/thumbs" in l:
                                            print("Do nothing")
                                        if "https://maps.eurac.edu/download/" in l:
                                            #print("Do nothing")
                                            id_collection = l.split("/")[-1]                                        
                                            metadata_detail['url_repository'] = "https://maps.eurac.edu/catalogue/#/dataset/"+id_collection
                                        else:
                                            #print(l)
                                            tmp = l.replace("https://maps.eurac.edu/", "").split("?")
                                            #print(tmp)
                                            for k in tmp[1].split('&'):
                                                #tmpk = k.split("&")
                                                if "format_options" in k:
                                                    url_objects.append(dict(l=l,file_type=k.replace("format_options=", "").replace("%2F", " ")
                                                                            .replace("%3A", " ")
                                                                            .replace("%3B", " ")
                                                                            .replace("%3D", " ")))
                                                    #print(k)
                            if 'format' in e:
                                if caption_category == "Maps":
                                    if "https://maps.eurac.edu/" in l:
                                        if "https://maps.eurac.edu/uploaded/thumbs" in l:
                                            print("Do nothing")
                                        if "https://maps.eurac.edu/download/" in l:
                                            #print("Do nothing")
                                            id_collection = l.split("/")[-1]                                        
                                            metadata_detail['url_repository'] = "https://maps.eurac.edu/catalogue/#/dataset/"+id_collection
                                        else:
                                            #print(l)
                                            tmp = l.replace("https://maps.eurac.edu/", "").split("?")
                                            #print(tmp)
                                            for k in tmp[1].split('&'):
                                                #tmpk = k.split("&")
                                                if "format" in k:
                                                    url_objects.append(dict(l=l,file_type=k.replace("format=", "").replace("%2F", " ")
                                                                            .replace("%3A", " ")
                                                                            .replace("%3B", " ")
                                                                            .replace("%3D", " ")))
                                                    #print(k)
                                        
                                else:
                                    print("Do nothing")
                                    #url_objects.append(dict(l=l,file_type=e[13:]))
                    else:
                        if caption_category == "STAC":
                            if "https://stac.eurac.edu:8080/collections/" in l:
                                id_collection = l.replace("https://stac.eurac.edu:8080/collections/", "").split("?")
                                metadata_detail['url_repository'] = l
                                url_objects.append(dict(l=l,file_type=id_collection[0]))
                            if "https://stac.eurac.edu/browser/#/collections/" in l:
                                id_collection = l.replace("https://stac.eurac.edu/browser/#/collections/", "").split("?")                                   
                                metadata_detail['url_repository'] = l
                                url_objects.append(dict(l=l,file_type=id_collection[0]))
                            elif "scientificnet-my.sharepoint.com" in l:
                                url_objects.append(dict(l=l,file_type="Sharepoint"))
                            else:
                                url_objects.append(dict(l=l,file_type=""))
                        # else:
                        #     print(l)
                        #     url_objects.append(dict(l=l,file_type=""))
            if type(metadataRecords['linkUrlProtocolWWWDOWNLOAD10httpdownload']) is str:
                #url_objects.append(dict(l=metadataRecords['linkUrlProtocolWWWDOWNLOAD10httpdownload'],file_type=""))
                if caption_category == "Other":
                    if "github" in metadataRecords['linkUrlProtocolWWWDOWNLOAD10httpdownload']:
                        tmp = metadataRecords['linkUrlProtocolWWWDOWNLOAD10httpdownload'].split("/")
                        #print(tmp)
                        url_objects.append(dict(l=metadataRecords['linkUrlProtocolWWWDOWNLOAD10httpdownload'],file_type=tmp[-1]))
                else:
                    url_objects.append(dict(l=metadataRecords['linkUrlProtocolWWWDOWNLOAD10httpdownload'],file_type=""))
                #metadata_detail['url_objects'] = metadataRecords['linkUrlProtocolWWWDOWNLOAD10httpdownload']
            #print(url_objects)
            metadata_detail['url_objects'] = sorted(url_objects, key=lambda d: d['l'])
        #print(len(metadata_detail['url_objects']))
        #print(metadata_detail)
        return metadata_detail
     

def get_total_number_metadata(request, url_geometry_part):
    url = GEONETWORK_BASE_URL + "/srv/eng/q?_content_type=json&summaryOnly=1&"+url_geometry_part
    #print(url)
    results = requests.get(url)
    summary_results = ast.literal_eval(JsonResponse(results.json(), safe=False).content.decode("utf-8"))
    #print(summary_results)
    if '@count' in str(summary_results):
        return (summary_results[0]['@count'])
    else:
        return(0)


def get_info_publication_complete(uuid):
    #print(uuid)
    creators = []
    rights = []
    type = "" 
    publisher = ""
    url = "https://api.datacite.org/graphql"
    body = """query Publication {
                publication(id: "10.48784/"""+uuid+"""") {
                    schemaOrg
                    type
                    creators {
                        familyName
                        givenName
                        id
                        name
                        type
                    }
                    doi
                    rights {
                        lang
                        rights
                        rightsIdentifier
                        rightsIdentifierScheme
                        rightsUri
                        schemeUri
                    }
                    publisher
            }   
            }"""

    response = requests.post(url=url, json={"query":body})

    json_response = response.content.decode('utf-8')
    if uuid in json_response:
        publication = json.loads(json_response)["data"]["publication"]
        #print("------------------------------------------------")
        #print(publication)
        if publication["creators"]:
            for a in publication["creators"]:
                creators.append(dict(id = a["id"], name = a["name"], type = a["type"]))

        rights = []
        for r in publication["rights"]:
            #print(r)
            rights.append(dict(uri = r["rightsUri"], rights = r["rights"], rightsIdentifier = r['rightsIdentifier']))
        type = publication["type"]
        publisher = publication["publisher"]
    return creators, rights, type, publisher


def get_info_publication(uuid):
    #print(uuid)
    authors = []
    type = ""
    rights = []
    doi_exists = False

    url = "https://api.datacite.org/graphql"
    body = """query Publication {
                publication(id: "10.48784/"""+uuid+"""") {
                    schemaOrg
                    type
                    creators {
                        familyName
                        givenName
                        id
                        name
                        type
                    }
                    doi
                    rights {
                        lang
                        rights
                        rightsIdentifier
                        rightsIdentifierScheme
                        rightsUri
                        schemeUri
                    }
            }   
            }"""

    response = requests.post(url=url, json={"query":body})

    json_response = response.content.decode('utf-8')
    if uuid in json_response:
        doi_exists = True
        publication = json.loads(json_response)["data"]["publication"]
        authors = []
        
        if publication["creators"]:
            for a in publication["creators"]:
                #print("publication "+a)
                if a["id"]:
                    authors.append(dict(href = a["id"]))
                    #print(a["id"])
                #authors.append('{ "href": "'+a["id"]+'" }')

        rights = []
        if publication["rights"]:
            for r in publication["rights"]:
                rights.append(dict(href = r["rightsUri"]))
                #rights.append('{ "href": "'+r["rightsUri"]+'" }') 
            #print(authors)
        
        if publication["type"]:
            type = publication["type"]
    
    return authors, type, rights, doi_exists

    #print(publication)
    
    

def get_collection_id(uuid, category):
    name_collection = GeonetworkMetadata.objects.filter(uuid=uuid, category=category).values("name_collection")
    #print(tmp_category_list)
    return name_collection[0]['name_collection']

def get_category(uuid):
        category = GeonetworkMetadata.objects.filter(uuid=uuid).values("category")
        return category[0]['category']

def get_name(uuid):
        name = GeonetworkMetadata.objects.filter(uuid=uuid).values("title")
        return name[0]['title']

def CheckSWHIDURL(url):
    try:
        #("CheckSWHIDURL"+url)
        response = requests.head(url)
        print(response)
        return response.status_code == 200
    except requests.RequestException:
        print(requests.RequestException)
        return False

def get_swhid(uuid):
    url = GEONETWORK_BASE_URL + "/srv/api/search/records/_search"
    swhid = ""
    #print("get_swhid2"+url)
    body = "{\"query\":{\"bool\":{\"must\":[{\"multi_match\":{\"query\":\""+uuid+"\",\"fields\":[\"id\",\"uuid\"]}},{\"terms\":{\"isTemplate\":[\"n\",\"y\"]}},{\"terms\":{\"draft\":[\"n\",\"y\",\"e\"]}}]}}}"
    headers = {'ACCEPT': ACCEPT_HTTP, 'CONTENT-TYPE': CONTENT_TYPE}
    results = requests.post(url, data=body, headers=headers)
    tmp = json.loads(results.text)
    #print(tmp)
    metadataRecords = tmp['hits']['hits'][0]['_source']
    #print(metadataRecords)
    if 'resourceIdentifier' in metadataRecords: 
        #print("resourceIdentifier "+metadataRecords['resourceIdentifier'][0]['codeSpace'])
        if CheckSWHIDURL(metadataRecords['resourceIdentifier'][0]['codeSpace']):
            swhid_link = json.loads(requests.get(metadataRecords['resourceIdentifier'][0]['codeSpace']).text)
            #print(swhid_link)        
            #print(swhid_link['links'])
            for e in swhid_link['links']:
                if e['title'] == "SWHID":
                    if "swh" in e['href']:
                        swhid = e['href']
        else:
            print("url invalid")
    return swhid

#Signposting linkset
def get_linkset(request, uuid):
    linkset_body = dict()
    
    authors, type, rights, doi_exists = get_info_publication(uuid)
    
    category = get_category(uuid)   

    swhid = get_swhid(uuid)
    #print("get_linkset "+swhid)

    describedby = []

    if category == 'OpenEO':
        name_collection = get_collection_id(uuid, category)   
        describedby.append(dict(href =  OPENEO_URL + name_collection, type = "application/json"))
    #geonetowrk url
    describedby.append(dict(href = GEONETWORK_URL + uuid + "/formatters/xml?approved=true", type = "application/rdf+xml"))  

    if doi_exists:
        #datacite api url
        describedby.append(dict(href = DATA_CITE_API + uuid, type = "application/json"))

    if authors:
        linkset_body["author"] = authors
    if rights:
        linkset_body["license"] = rights

    #print(swhid)
    if swhid:
        linkset_body["http://www.w3.org/ns/prov#wasAttributedTo"] = dict(href="https://archive.softwareheritage.org/"+ swhid,type = "text/html")

    linkset_body["anchor"] = EDP_DISCOVERY_URL + uuid    
    linkset_body["describedby"] = describedby

    if doi_exists == False and (category == 'Maps' or category == 'SOS' or category == 'PostgresDB' or category == 'InfluxDB'):
        linkset_body["type"] = [dict(href = "https://schema.org/Dataset"), dict(href = "https://schema.org/AboutPage")]
    else:
        linkset_body["type"] = [dict(href = "https://schema.org/" + type), dict(href = "https://schema.org/AboutPage")]
    
    if doi_exists:
        linkset_body["cite-as"] = dict(href = DOI_URL + uuid)
        #linkset_body["cite-as"] = linkset_body["cite_as"]
        #del linkset_body["cite_as"]
    
    linkset = dict(linkset = linkset_body)
    #print(linkset)

    #print(linkset_json)
    return JsonResponse(linkset, safe=False, status=200)


#jsonld
def get_jsonld(request, uuid):

    jsonld = dict()
    authors, type, rights, doi_exists = get_info_publication(uuid)
    
    category = get_category(uuid)   

    describedby = []
    reverse = dict()    
    isPartOf = dict()
    citation = dict()
    if category == 'OpenEO':
        name_collection = get_collection_id(uuid, category)   
        describedby.append(dict(href =  OPENEO_URL + name_collection, type = "application/json"))
    #geonetowrk url
    describedby.append(dict(href = GEONETWORK_URL + uuid + "/formatters/xml?approved=true", type = "application/rdf+xml"))  

    if doi_exists:
        #datacite api url
        describedby.append(dict(href = DATA_CITE_API + uuid, type = "application/json"))

    jsonld["@context"] = "https://schema.org/"    

    if authors:
        jsonld["creator"] = authors

    jsonld["name"] = get_name(uuid)

    jsonld["isAccessibleForFree"] = False
    if rights:
        jsonld["license"] = rights
    #Should be dynamic and not hardcoded here
    jsonld["conditionsOfAccess"] = "restricted"

    if doi_exists == False and (category == 'Maps' or category == 'SOS' or category == 'PostgresDB' or category == 'InfluxDB'):
        #Should arrive from the database and not hardcoded here
        jsonld["@type"] = "Dataset"
    else:
        if type:
            jsonld["@type"] = type
    
    if doi_exists:
        jsonld["@id"] = DOI_URL + uuid
        jsonld["identifier"] = DOI_URL + uuid
        jsonld["url"] = EDP_DISCOVERY_URL + uuid
    
    
    size = dict()
    distribution = dict()

    #Should be dynamic and not hardcoded here
    distribution["@type"] = "DataDownload"
    if category == "Maps":
        distribution["encodingFormat"] = "application/gzip"
        distribution["contentUrl"] = DOI_URL + uuid
        isPartOf["@type"] = "CreativeWork"
        if type:
            isPartOf["name"] = type
        reverse["@id"] = "https://doi.org/10.25504/FAIRsharing.8ee7f1"
        reverse["identifier"] = "https://doi.org/10.25504/FAIRsharing.8ee7f1"
        citation["@id"] = "https://doi.org/10.25504/FAIRsharing.8ee7f1"
        citation["identifier"] = "https://doi.org/10.25504/FAIRsharing.8ee7f1"
        citation["url"] = "https://doi.org/10.25504/FAIRsharing.8ee7f1"
    if category == "OpenEO":
        # it is not completely true because the URL is the endpoint of the API of openEO
        distribution["encodingFormat"] = "application/json"
        distribution["fileFormat"] = "application/json"
        distribution["contentUrl"] = OPENEO_URL + name_collection
        size["@type"] = "Timeseries"
        isPartOf["@type"] = "CreativeWork"
        if type:
            isPartOf["name"] = type
        reverse["@id"] = "https://doi.org/10.25504/FAIRsharing.f9de28"
        reverse["identifier"] = "https://doi.org/10.25504/FAIRsharing.f9de28"
        citation["@id"] = "https://doi.org/10.25504/FAIRsharing.f9de28"
        citation["identifier"] = "https://doi.org/10.25504/FAIRsharing.f9de28"
        citation["url"] = "https://doi.org/10.25504/FAIRsharing.8ee7f1"
    if category == "PostgresDB" or category == "InfluxDB":
        if type:
            size["@type"] = type
        #Hardcoded but to modify
        distribution["encodingFormat"] = "application/json"
        distribution["fileFormat"] = "application/json"
        distribution["contentUrl"] = "Custom API"
    if category == "SOS":
        distribution["encodingFormat"] = ""
        distribution["fileFormat"] = ""
        distribution["contentUrl"] = DOI_URL + uuid
    
    if distribution:
        jsonld["distribution"] = distribution   
    
    if type:
        size["unitText"] = type
        citation["@type"] = ["CreativeWork", type]
        jsonld["citation"] = citation

    if size:
        jsonld["size"] = size

    if isPartOf:
        reverse["isPartOf"] = isPartOf
        jsonld["@reverse"] = reverse
    
    jsonld["inLanguage"] = "en"

    swhid = get_swhid(uuid)
    #print(swhid)
    if swhid:
        swhid_dict = dict(href = "https://archive.softwareheritage.org/"+swhid, type = "text/html")#title = "SWHID")
        jsonld["http://www.w3.org/ns/prov#wasAttributedTo"] = swhid_dict

    #print(jsonld)
    #linkset = dict(linkset = jsonld)
    #print(linkset)
    #print(linkset_json)
    return JsonResponse(jsonld, safe=False, status=200)