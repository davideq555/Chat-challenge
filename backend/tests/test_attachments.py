import pytest
from fastapi import status

def test_create_attachment(client):
    """Test crear un nuevo adjunto"""
    response = client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file.jpg",
        "file_type": "image/jpeg"
    })
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["message_id"] == 1
    assert data["file_url"] == "https://example.com/file.jpg"
    assert data["file_type"] == "image/jpeg"
    assert "id" in data
    assert "uploaded_at" in data

def test_get_all_attachments(client):
    """Test obtener todos los adjuntos"""
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file1.jpg",
        "file_type": "image/jpeg"
    })
    client.post("/attachments/", json={
        "message_id": 2,
        "file_url": "https://example.com/file2.pdf",
        "file_type": "application/pdf"
    })

    response = client.get("/attachments/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2

def test_get_attachments_filter_by_message(client):
    """Test filtrar adjuntos por mensaje"""
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file1.jpg",
        "file_type": "image/jpeg"
    })
    client.post("/attachments/", json={
        "message_id": 2,
        "file_url": "https://example.com/file2.jpg",
        "file_type": "image/jpeg"
    })
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file3.pdf",
        "file_type": "application/pdf"
    })

    response = client.get("/attachments/?message_id=1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert all(att["message_id"] == 1 for att in data)

def test_get_attachments_filter_by_type(client):
    """Test filtrar adjuntos por tipo"""
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file1.jpg",
        "file_type": "image/jpeg"
    })
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file2.pdf",
        "file_type": "application/pdf"
    })
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file3.jpg",
        "file_type": "image/jpeg"
    })

    response = client.get("/attachments/?file_type=image/jpeg")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert all(att["file_type"].lower() == "image/jpeg" for att in data)

def test_get_attachments_filter_type_case_insensitive(client):
    """Test que el filtro por tipo es case insensitive"""
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file1.jpg",
        "file_type": "IMAGE/JPEG"
    })

    response = client.get("/attachments/?file_type=image/jpeg")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1

def test_get_attachment_by_id(client):
    """Test obtener adjunto por ID"""
    create_response = client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file.jpg",
        "file_type": "image/jpeg"
    })
    attachment_id = create_response.json()["id"]

    response = client.get(f"/attachments/{attachment_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == attachment_id
    assert data["file_url"] == "https://example.com/file.jpg"

def test_get_attachment_not_found(client):
    """Test obtener adjunto que no existe"""
    response = client.get("/attachments/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Attachment not found" in response.json()["detail"]

def test_update_attachment(client):
    """Test actualizar adjunto"""
    create_response = client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/old.jpg",
        "file_type": "image/jpeg"
    })
    attachment_id = create_response.json()["id"]

    response = client.put(f"/attachments/{attachment_id}", json={
        "file_url": "https://example.com/new.jpg",
        "file_type": "image/png"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["file_url"] == "https://example.com/new.jpg"
    assert data["file_type"] == "image/png"

def test_update_attachment_partial(client):
    """Test actualización parcial de adjunto"""
    create_response = client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file.jpg",
        "file_type": "image/jpeg"
    })
    attachment_id = create_response.json()["id"]

    # Solo actualizar URL
    response = client.put(f"/attachments/{attachment_id}", json={
        "file_url": "https://example.com/new.jpg"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["file_url"] == "https://example.com/new.jpg"
    assert data["file_type"] == "image/jpeg"  # No cambió

def test_update_attachment_not_found(client):
    """Test actualizar adjunto que no existe"""
    response = client.put("/attachments/999", json={
        "file_url": "https://example.com/new.jpg"
    })
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_attachment(client):
    """Test eliminar adjunto"""
    create_response = client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file.jpg",
        "file_type": "image/jpeg"
    })
    attachment_id = create_response.json()["id"]

    response = client.delete(f"/attachments/{attachment_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que el adjunto ya no existe
    get_response = client.get(f"/attachments/{attachment_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_attachment_not_found(client):
    """Test eliminar adjunto que no existe"""
    response = client.delete("/attachments/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_message_attachments(client):
    """Test obtener todos los adjuntos de un mensaje"""
    # Crear adjuntos para diferentes mensajes
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file1.jpg",
        "file_type": "image/jpeg"
    })
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file2.pdf",
        "file_type": "application/pdf"
    })
    client.post("/attachments/", json={
        "message_id": 2,
        "file_url": "https://example.com/file3.jpg",
        "file_type": "image/jpeg"
    })

    response = client.get("/attachments/message/1/all")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert all(att["message_id"] == 1 for att in data)

def test_get_message_attachments_empty(client):
    """Test obtener adjuntos de mensaje sin adjuntos"""
    response = client.get("/attachments/message/999/all")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0

def test_count_message_attachments(client):
    """Test contar adjuntos de un mensaje"""
    # Crear adjuntos
    for i in range(3):
        client.post("/attachments/", json={
            "message_id": 1,
            "file_url": f"https://example.com/file{i}.jpg",
            "file_type": "image/jpeg"
        })

    response = client.get("/attachments/message/1/count")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message_id"] == 1
    assert data["attachment_count"] == 3

def test_count_message_attachments_zero(client):
    """Test contar adjuntos de mensaje sin adjuntos"""
    response = client.get("/attachments/message/999/count")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message_id"] == 999
    assert data["attachment_count"] == 0

def test_get_attachments_stats_by_type(client):
    """Test obtener estadísticas de adjuntos por tipo"""
    # Crear varios adjuntos de diferentes tipos
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file1.jpg",
        "file_type": "image/jpeg"
    })
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file2.jpg",
        "file_type": "image/jpeg"
    })
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file3.pdf",
        "file_type": "application/pdf"
    })
    client.post("/attachments/", json={
        "message_id": 1,
        "file_url": "https://example.com/file4.png",
        "file_type": "image/png"
    })

    response = client.get("/attachments/stats/by-type")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_attachments"] == 4
    assert data["by_type"]["image/jpeg"] == 2
    assert data["by_type"]["application/pdf"] == 1
    assert data["by_type"]["image/png"] == 1

def test_get_attachments_stats_empty(client):
    """Test estadísticas cuando no hay adjuntos"""
    response = client.get("/attachments/stats/by-type")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_attachments"] == 0
    assert data["by_type"] == {}
