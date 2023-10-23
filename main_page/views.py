from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.http import JsonResponse
import requests
import json 
import ast, re
import psycopg2
from .models import DocSource, SnippetCode, GeonetworkMetadata

ACCEPT_HTTP = "application/json"
CONTENT_TYPE = "application/json"
EDP_DISCOVERY_URL = 'http://10.8.244.240:8081/discovery/'
DOI_URL = 'https://doi.org/10.48784/'
OPENEO_URL = 'https://openeo.eurac.edu/collections/'

class DocsPageView(generic.ListView):
    template_name = 'docs.html'
    context_object_name = 'latest_docs_sources_list'

    def get_queryset(self):
        """Return the last five published docs sources."""
        return DocSource.objects.all()
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
        print(request.GET)
        conn = psycopg2.connect(
                database="edp_portal_gui", user='edp_gui_user', password='73bd357832012a62357095bf6d9324f8', host='10.8.244.39', port='5432'
            )
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
        # if request.GET.get('box'):            
        #     boundingbox = request.GET.get('box')
        #     boundingbox = boundingbox.split(",")
        #     #print(boundingbox)
        #     polygon = ""
        #     for i in range(len(boundingbox)):
        #         if i == 0:
        #             polygon = polygon + boundingbox[i]
        #         else:
        #             if i % 2 == 0:
        #                 polygon = polygon + "," + boundingbox[i]
        #             elif i%2 != 0:
        #                 polygon = polygon + " " + boundingbox[i]
        #     #print(polygon)
        #     polygon = "POLYGON((" + polygon + "))"      
        #     if "all" not in where_clause_array:
        #         final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_CONTAINS(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
        #     else:
        #         final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_CONTAINS(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) ORDER BY title ASC"
        #     print(final_query)
        #     cursor.execute(final_query)
        #     #print(conn.commit())
        #     results = cursor.fetchall()
        #     return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
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

            print('where_clause_array')
            print(where_clause_array)
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
            #print("KEYWORD " + searchKeyword)

            # if "all" not in where_clause_array:
            #     final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
            # else:
            #     final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' ORDER BY title ASC"
            #print(title_list)
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
    #finally:
    #    metadata_results = GeonetworkMetadata.objects.all()    
    #    return render(request, 'discovery.html', {'metadata_results': metadata_results, 'title_list': title_list})
    #print("finally")
    cursor.close()
    conn.close()
    metadata_results = GeonetworkMetadata.objects.order_by('title')
    #print(title_list)    
    print(type(metadata_results))
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

def result_detail(request, uuid):
    metadata_details = get_metadata_details(request, uuid)
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

        context = {
            "uuid" : uuid,
            #"result_json" : result_json["metadata"],
            "result_json" : metadata_details,
            "snippet_code_list" : snippet_code_list,
            "docs_list" : docs_list
            #'title': result_json["metadata"]["title"],
        }
        response = render(request, 'result_detail.html', context)
        #Signposting HTTP HEAD Link <https://example.org/linkset/7507/lset> ; rel="linkset" ; type="application/linkset" , 
        response['Link'] = '<' + EDP_DISCOVERY_URL + "linkset/" + uuid + '> ; rel="linkset" ; type="application/linkset+json"'
        return response
    else:
        #print(metadata_details)
        context = {
            "error" : "No metadata found for this uuid (" + uuid + ")"
        }

        return render(request, 'result_detail.html', context)

def get_metadata_details(request, uuid):
    try:
        metadata_detail = {}
        #url = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&_draft=y+or+n+or+e&_isTemplate=y+or+n&fast=index&uuid="+uuid
        url = "https://edp-portal.eurac.edu/geonetwork/srv/api/search/records/_search"
        print(url)
        body = "{\"query\":{\"bool\":{\"must\":[{\"multi_match\":{\"query\":\""+uuid+"\",\"fields\":[\"id\",\"uuid\"]}},{\"terms\":{\"isTemplate\":[\"n\",\"y\"]}},{\"terms\":{\"draft\":[\"n\",\"y\",\"e\"]}}]}}}"
        headers = {'ACCEPT': ACCEPT_HTTP, 'CONTENT-TYPE': CONTENT_TYPE}
        results = requests.post(url, data=body, headers=headers)
        tmp = json.loads(results.text)
        metadataRecords = tmp['hits']['hits'][0]['_source']
        #print(metadataRecords)

        if 'contact' in metadataRecords:
            for contact in metadataRecords['contact']:
                if 'pointOfContact' in contact['role']:
                    metadata_detail['contactMetadata'] = { 'contactName' : contact['organisation'], 'email' : contact['email'], 'address' : contact['address'] }
                if 'author' in contact['role']:
                    metadata_detail['contactResource'] = { 'contactName' : contact['organisation'], 'email' : contact['email'], 'address': contact['address'] }

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

        if 'overview' in metadataRecords:
            metadata_detail['thumbnail'] = metadataRecords['overview'][0]['url']

        gn_cat = GeonetworkMetadata.objects.filter(uuid=uuid)
        print(gn_cat[0].category)
        metadata_detail['category'] = gn_cat[0].category

        if gn_cat[0].doi:
            metadata_detail['doi'] = gn_cat[0].doi
        if gn_cat[0].citation:
            metadata_detail['citation'] = gn_cat[0].citation
        if gn_cat[0].supplemental_information:
            metadata_detail['supplemental_information'] = gn_cat[0].supplemental_information
        #if 'cat' in metadataRecords:
        #    if metadataRecords['cat'] == 'OpenEO':
        #        metadata_detail['category'] = 'OpenEO'
        #    elif metadataRecords['cat'] == 'SOS':
        #        metadata_detail['category'] = 'SOS'
        #    elif metadataRecords['cat'] == 'maps':
        #        metadata_detail['category'] = 'Maps'
        #    else:
        #        metadata_detail['category'] = 'Database'
        

        if 'tag' in metadataRecords:
            keywords = []
            for t in metadataRecords['tag']:        
                keywords.append(t['default'])   
            metadata_detail['keyword'] = ", ".join(keywords)

        if 'lineage' in metadataRecords:
            metadata_detail['lineage'] = metadataRecords['lineageObject']

        if 'resourceTemporalExtentDetails' in metadataRecords:
            metadata_detail['tempExtentBegin'] = metadataRecords['resourceTemporalExtentDetails'][0]['start']['date']
            metadata_detail['tempExtentEnd'] = metadataRecords['resourceTemporalExtentDetails'][0]['end']['date']

        if 'link' in metadataRecords:
            metadata_detail['name_collection'] = metadataRecords['link'][0]['name']
        
        print(metadata_detail)
        return metadata_detail
        
    except:
        error = {}
        error['error'] = "Some errors occurred: no metadata found or problems in parsing metadata."
        return error

def get_total_number_metadata(request, url_geometry_part):
    url = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&summaryOnly=1&"+url_geometry_part
    results = requests.get(url)
    summary_results = ast.literal_eval(JsonResponse(results.json(), safe=False).content.decode("utf-8"))
    #print(summary_results)
    if '@count' in str(summary_results):
        return (summary_results[0]['@count'])
    else:
        return(0)


def get_info_publication(uuid):
    #print(uuid)
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
    publication = json.loads(json_response)["data"]["publication"]
    #print(publication)
    
    authors = []
    for a in publication["creators"]:
        authors.append(dict(href = a["id"]))
        #authors.append('{ "href": "'+a["id"]+'" }')

    rights = []
    for r in publication["rights"]:
        rights.append(dict(href = r["rightsUri"]))
        #rights.append('{ "href": "'+r["rightsUri"]+'" }') 
    #print(authors)
    return authors, publication["type"], rights

def get_collection_id(uuid):
    tmp_category_list = GeonetworkMetadata.objects.filter(uuid=uuid, category="OpenEO").values("name_collection")
    print(tmp_category_list)

#Signposting linkset
def get_linkset(request, uuid):

    authors, type, rights = get_info_publication(uuid)
    #category = get_collection_id(uuid)


    id_collection = ""
    describedby = []
    describedby.append(dict(href =  OPENEO_URL + id_collection, type = "application/json"))
    describedby.append(dict(href = "https://edp-portal.eurac.edu/geonetwork/srv/api/records/" + uuid + "/formatters/xml?approved=true", type = "application/rdf+xml"))  
    describedby.append(dict(href = "https://api.datacite.org/dois/10.48784/" + uuid, type = "application/json"))

    linkset_body = dict(anchor = EDP_DISCOVERY_URL + uuid,
                   cite_as = dict(href = DOI_URL + uuid),
                   type = [dict(href = "https://schema.org/" + type), dict(href = "https://schema.org/AboutPage")],
                   author = authors,
                   describedby = describedby,
                   license = rights
                   )
    
    linkset_body["cite-as"] = linkset_body["cite_as"]
    del linkset_body["cite_as"]
    
    linkset = dict(linkset = linkset_body)
    #print(linkset)
    
    
    # linkset_start = '{"linkset":[ { '
    
    # anchor= '"anchor": "'+ BASE_URL + uuid + '",'     
    
    # cite_as = '"cite-as": [ { "href": "' + DOI_URL + uuid + '" } ]'

    # type = '"type": [ { "href": "https://schema.org/' + type + '" }, { "href": "https://schema.org/AboutPage" } ]'
    
    # author = '"author": [ '+(",").join(authors)+' ]'

    # id_collection = ""

    # describedby = '"describedby": [ { "href": "' + OPENEO_URL + id_collection + '", "type": "application/json" }, { "href": "https://edp-portal.eurac.edu/geonetwork/srv/api/records/'+uuid+'/formatters/xml?approved=true", "type": "application/rdf+xml" }, { "href": "https://api.datacite.org/dois/10.48784/'+uuid+'", "type": "application/vnd.datacite.datacite+json" }]'
    
    # license = '"license": [ '+(",").join(rights)+' ]'

    # linkset_close = '}]}'

    # linkset_json = linkset_start + anchor + "," + cite_as + "," + type + "," + author + "," + describedby + "," + license + linkset_close

    #print(linkset_json)
    return JsonResponse(linkset, safe=False, status=200)