from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from starlette import status
from database import get_db, MovieModel
from schemas import MovieDetailResponseSchema
from schemas.movies import MoviePaginatedResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=MoviePaginatedResponseSchema)
async def get_movies(
    request: Request,
    page: Annotated[
        int,
        Query(ge=1, description="Page number"),
    ] = 1,
    per_page: Annotated[
        int,
        Query(
            ge=1,
            le=20,
        ),
    ] = 10,
    db: AsyncSession = Depends(get_db),
):

    offset = (page - 1) * per_page
    limit = per_page
    stmt = select(MovieModel).offset(offset).limit(limit)
    total_items = await db.scalar(func.count(MovieModel.id))
    movies = await db.scalars(stmt)
    all_movies = movies.all()

    if not all_movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    total_pages = int(total_items) // per_page + 1
    base_path = request.url.path

    prev_page = (
        (f"{base_path}?page={page - 1}&per_page={per_page}") if page > 1 else None
    )

    next_page = (
        (f"{base_path}?page={page + 1}&per_page={per_page}")
        if page < total_pages
        else None
    )

    if page < 1 or page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE,
            detail=[
                {
                    "loc": ["query", "page"],
                    "msg": "Ensure this value is greater than or equal to 1",
                    "type": "value_error.number.not_ge",
                }
            ],
        )

    return {
        "movies": all_movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{id}/", response_model=MovieDetailResponseSchema)
async def get_detail_movie(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == id)
    movie = await db.scalar(stmt)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return movie
