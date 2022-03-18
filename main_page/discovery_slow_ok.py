# def discovery(request):
#     context = {}
#     #print("request body:" + request.body.decode("utf-8"))
#     #print(request)
#     search_request = ''

#     if(request.body):
#         #search_request = json.loads(request.body)
#         search_request = json.loads(request.body.decode("utf-8"))
#         #print(len(search_request['boundingbox']))
#         #if(search_request['boundingbox']):
#         #    print(search_request['boundingbox'])
#     if 'term' in request.GET:  
#         print("term")  
#         metadata_title_list = get_list_metadata_title(request)
#         topic_list = get_topic_list(request)
#         print(topic_list+metadata_title_list)
#         title_list = topic_list+metadata_title_list
#         if (len(title_list) == 0):
#             title_list = ['no title found']
        
#         return JsonResponse((title_list), safe=False, status=200)
    
#     #if 'boundingbox' in str(request.body):
#     if request.GET.get('box') == "true":
#         print("search ONLY BY boundingbox "+request.GET.get('box'))
#         polygon = json.loads(request.body)
#         #print(polygon['boundingbox'])      
#         metadata_results = get_results_bounding_box(request, polygon['boundingbox'])

#         context = {
#             'metadata_results': metadata_results,
#         }
#         return JsonResponse({'metadata_results': metadata_results}, safe=False, status=200)
#         #return render(request, 'discovery.html', context)

#     if request.GET.get('keybox') == 'false':
            
#         print("search ONLY BY keyword "+request.GET['search'])  
        
#         metadata_results = get_results_by_keyword(request, request.GET['search'])

#         context = {
#             'metadata_results': metadata_results,
#         }
#         return JsonResponse({'metadata_results': metadata_results}, safe=False, status=200)

#     if request.GET.get('keybox') == 'true':
#         print("BOTH SEARCH")
#         print(request.body.decode("utf-8"))    
#         search_request = json.loads(request.body)
#         polygon = search_request['boundingbox']
#         keyword = search_request['keyword']

#         metadata_results = get_results_bounding_box(request, polygon, keyword)

#         context = {
#             'metadata_results': metadata_results,
#         }
#         return JsonResponse({'metadata_results': metadata_results}, safe=False, status=200)       

#     print("exit without any if")   
#     return render(request, 'discovery.html', context)
    