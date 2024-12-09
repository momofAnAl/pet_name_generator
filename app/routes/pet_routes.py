from flask import Blueprint, request, abort, make_response
from ..db import db
from ..models.pet import Pet

import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

bp = Blueprint("pets", __name__, url_prefix="/pets")

@bp.post("")
def create_pet():
    request_body = request.get_json()
    
    try:
        new_pet = Pet.from_dict(request_body)
        db.session.add(new_pet)
        db.session.commit()
        
        return new_pet.to_dict(), 201
    
    except KeyError as e:
        abort(make_response({"message": f"missing required value: {e}"}, 400))

@bp.get("")
def get_pets():
    pet_query = db.select(Pet)

    pets = db.session.scalars(pet_query)
    response = []

    for pet in pets:
        response.append(pet.to_dict())

    return response

@bp.get("/<pet_id>")
def get_single_pet(pet_id):
    pet = validate_model(Pet,pet_id)
    return pet.to_dict()

@bp.post("/<pet_id>/generate")
def add_name(pet_id):
    pet_obj = validate_model(Pet, pet_id)
    
    if pet_obj.name:
        return {"message": f"Name already generated for {pet_obj.name}"}, 201
    
    name = generate_name(pet_obj)
    
    db.session.add(name)
    db.session.commit()
    
    return {"message": f"Name successfully added to {pet_obj.name}"}, 201
   
    
def generate_name(pet):
    model = genai.GenerativeModel("gemini-1.5-flash")
    input_message = f"I have a pet.\
    I have a pet who has following characteristic {pet.personality}.\
    My pet's color is {pet.color} and species is {pet.animal_type}.\
    Please generate a unique and creative name for my pet."
    
    response = model.generate_content(input_message)
    print(response)
    response_split = response.text
    
    return response_split
    
def validate_model(cls,id):
    try:
        id = int(id)
    except:
        response =  response = {"message": f"{cls.__name__} {id} invalid"}
        abort(make_response(response , 400))

    query = db.select(cls).where(cls.id == id)
    model = db.session.scalar(query)
    if model:
        return model

    response = {"message": f"{cls.__name__} {id} not found"}
    abort(make_response(response, 404))