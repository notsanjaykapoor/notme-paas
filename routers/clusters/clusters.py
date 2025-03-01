import fastapi
import fastapi.responses
import fastapi.templating
import sqlmodel

import context
import log
import main_shared
import models
import services.clusters
import services.clusters.requests
import services.hetzner.servers
import services.hetzner.ssh_keys
import services.users
import services.machines

logger = log.init("app")

# initialize templates dir
templates = fastapi.templating.Jinja2Templates(directory="routers", context_processors=[main_shared.jinja_context])

app = fastapi.APIRouter(
    tags=["app"],
    dependencies=[fastapi.Depends(main_shared.get_db)],
    responses={404: {"description": "Not found"}},
)


@app.get("/clusters")
def clusters_list(
    request: fastapi.Request,
    query: str = "",
    offset: int=0,
    limit: int=50,
    user_id: int = fastapi.Depends(main_shared.get_user_id),
    db_session: sqlmodel.Session = fastapi.Depends(main_shared.get_db),
):
    """
    List all clusters
    """
    logger.info(f"{context.rid_get()} clusters list query '{query}' try")

    if user_id == 0:
        return fastapi.responses.RedirectResponse("/login")

    user = services.users.get_by_id(db_session=db_session, id=user_id)

    clusters_list = []
    query_seconds = 0

    try:
        clusters_result = services.clusters.list(db_session=db_session, query=query, offset=offset, limit=limit)
        clusters_list = clusters_result.objects
        query_code = 0
        query_result = f"query '{query}' returned {len(clusters_list)} results in {query_seconds}s"

        logger.info(f"{context.rid_get()} clusters list query '{query}' ok")
    except Exception as e:
        query_code = 500
        logger.error(f"{context.rid_get()} clusters list exception '{e}'")

    if "HX-Request" in request.headers:
        template = "clusters/list_table.html"
    else:
        template = "clusters/list.html"

    try:
        response = templates.TemplateResponse(
            request,
            template,
            {
                "app_name": "Clusters",
                "clusters_list": clusters_list,
                "prompt_text": "search",
                "query": query,
                "query_code": query_code,
                "query_result": query_result,
                "user": user,
            }
        )
    except Exception as e:
        logger.error(f"{context.rid_get()} clusters list render exception '{e}'")
        return templates.TemplateResponse(request, "500.html", {})
    
    return response


@app.get("/clusters/{cluster_id}/machines")
def clusters_machines_list(
    request: fastapi.Request,
    cluster_id: int | str,
    query: str = "",
    user_id: int = fastapi.Depends(main_shared.get_user_id),
    db_session: sqlmodel.Session = fastapi.Depends(main_shared.get_db),
):
    """
    List all cluster machines.
    
    The cluster_id 'all' is reserved for listing all machines across all clusters.
    """
    if user_id == 0:
        return fastapi.responses.RedirectResponse("/login")

    logger.info(f"{context.rid_get()} cluster '{cluster_id}' query '{query}' try")

    machines_list = []
    query_code = 0
    query_result = ""
    query_seconds = 0

    user = services.users.get_by_id(db_session=db_session, id=user_id)

    try:
        if cluster_id == "all":
            cluster = models.Cluster(id=0, name="all")
            clusters_result = services.clusters.list(db_session=db_session, query=query, offset=0, limit=20)
            clusters_list = clusters_result.objects
            app_name = "Machines"
            query_search = 1
        else:
            cluster = services.clusters.get_by_id_or_name(db_session=db_session, id=cluster_id)
            clusters_list = [cluster]
            app_name = "Cluster Machines"
            query_search = 0

        for cluster_ in clusters_list:
            list_result = services.machines.list(cluster=cluster_)
            machines_list.extend(list_result.objects_list)
            query_seconds += list_result.seconds

        query_result = f"query '{query}' returned {len(machines_list)} results in {query_seconds}s"

        logger.info(f"{context.rid_get()} cluster '{cluster_id}' ok")
    except Exception as e:
        query_code = 500
        logger.error(f"{context.rid_get()} clusters '{cluster_id}' exception '{e}'")

    if "HX-Request" in request.headers:
        template = "machines/list_table.html"
    else:
        template = "machines/list.html"

    try:
        response = templates.TemplateResponse(
            request,
            template,
            {
                "app_name": app_name,
                "cluster": cluster,
                "machines_list": machines_list,
                "prompt_text": "search query - e.g. cluster:foo",
                "query": query,
                "query_code": query_code,
                "query_result": query_result,
                "query_search": query_search,
                "user": user,
            }
        )
    except Exception as e:
        logger.error(f"{context.rid_get()} clusters '{cluster_id}' render exception '{e}'")
        return templates.TemplateResponse(request, "500.html", {})
    
    return response


@app.get("/clusters/{cluster_id}/requests")
def clusters_requests(
    request: fastapi.Request,
    cluster_id: int | str,
    user_id: int = fastapi.Depends(main_shared.get_user_id),
    db_session: sqlmodel.Session = fastapi.Depends(main_shared.get_db),
):
    if user_id == 0:
        return fastapi.responses.RedirectResponse("/login")

    user = services.users.get_by_id(db_session=db_session, id=user_id)

    logger.info(f"{context.rid_get()} cluster '{cluster_id}' requests try")

    try:
        cluster = services.clusters.get_by_id_or_name(db_session=db_session, id=cluster_id)

        requests_result = services.clusters.requests.list(
            db_session=db_session,
            query=f"cluster_id:{cluster.id}",
            offset=0,
            limit=50,
        )
        requests_list = requests_result.objects

        logger.info(f"{context.rid_get()} clusters '{cluster_id}' requests ok")
    except Exception as e:
        logger.error(f"{context.rid_get()} clusters '{cluster_id}' requests exception '{e}'")

    if "HX-Request" in request.headers:
        template = "clusters/requests/list_table.html"
    else:
        template = "clusters/requests/list.html"

    try:
        response = templates.TemplateResponse(
            request,
            template,
            {
                "app_name": "Cluster Requests",
                "cluster": cluster,
                "prompt_text": "search",
                "requests_list": requests_list,
                "user": user,
            }
        )
    except Exception as e:
        logger.error(f"{context.rid_get()} clusters '{cluster_id}' requests render exception '{e}'")
        return templates.TemplateResponse(request, "500.html", {})
    
    return response


@app.get("/clusters/{cluster_id}/scale")
def clusters_scale(
    request: fastapi.Request,
    cluster_id: int | str,
    ask: int,
    machine_name: str="",
    user_id: int = fastapi.Depends(main_shared.get_user_id),
    db_session: sqlmodel.Session = fastapi.Depends(main_shared.get_db),
):
    """
    Add cluster request to scale machines based on 'ask' param.
    """
    if user_id == 0:
        return fastapi.responses.RedirectResponse("/login")

    logger.info(f"{context.rid_get()} cluster '{cluster_id}' ask {ask} machine '{machine_name}' try")

    try:
        cluster = services.clusters.get_by_id_or_name(db_session=db_session, id=cluster_id)

        cluster_data = {}

        if machine_name:
            cluster_data["machine_name"] = machine_name

        request_result = services.clusters.requests.add(
            db_session=db_session,
            cluster_id=cluster.id,
            cluster_ask=ask,
            data=cluster_data,
        )

        if request_result.code == 0:
            logger.info(f"{context.rid_get()} cluster '{cluster_id}' ask {ask} ok")
        else:
            logger.error(f"{context.rid_get()} cluster '{cluster_id}' ask {ask} error - code {request_result.code}")
    except Exception as e:
        logger.error(f"{context.rid_get()} cluster '{cluster_id}' ask {ask} exception '{e}'")

    return fastapi.responses.RedirectResponse("/clusters")
