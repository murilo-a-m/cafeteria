-- =============================================================
-- Cafeteria Gourmet Delivery - Projeto fisico do banco (MySQL)
-- PIT II - Sistemas de Informacao
--
-- Obs: a aplicacao cria as tabelas sozinha (db.create_all()) mas
-- deixei o script aqui pra documentacao e pra quem quiser criar na mao.
-- =============================================================

CREATE DATABASE IF NOT EXISTS cafeteria DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cafeteria;

-- usuarios do sistema (cliente, atendente e admin ficam na mesma tabela)
CREATE TABLE users (
    id              INT NOT NULL AUTO_INCREMENT,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(120) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    phone           VARCHAR(20),
    `role`          VARCHAR(20) NOT NULL DEFAULT 'cliente',
    active          BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_users_email (email),
    CONSTRAINT ck_users_role CHECK (`role` IN ('cliente', 'atendente', 'admin'))
) ENGINE=InnoDB;

CREATE TABLE addresses (
    id          INT NOT NULL AUTO_INCREMENT,
    user_id     INT NOT NULL,
    cep         VARCHAR(9) NOT NULL,
    street      VARCHAR(150) NOT NULL,
    number      VARCHAR(10) NOT NULL,
    complement  VARCHAR(60),
    district    VARCHAR(80),
    city        VARCHAR(80),
    state       CHAR(2),
    PRIMARY KEY (id),
    CONSTRAINT fk_addresses_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB;

-- log de login/logout (US15)
CREATE TABLE access_logs (
    id          INT NOT NULL AUTO_INCREMENT,
    user_id     INT NULL,           -- null quando o login falha com email que nao existe
    email       VARCHAR(120),
    action      VARCHAR(30),
    ip          VARCHAR(45),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_logs_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB;

CREATE TABLE products (
    id          INT NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    price       DECIMAL(10,2) NOT NULL,
    category    VARCHAR(20) NOT NULL,     -- bebidas, doces, salgados, kits
    image       VARCHAR(200),
    available   BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT ck_products_price CHECK (price > 0)
) ENGINE=InnoDB;

CREATE TABLE orders (
    id              INT NOT NULL AUTO_INCREMENT,
    user_id         INT NOT NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'aguardando_pagamento',
    address_text    VARCHAR(300) NOT NULL,   -- copia do endereco no momento da compra
    cep             VARCHAR(9),
    payment_method  VARCHAR(10),             -- pix, credito, debito
    payment_status  VARCHAR(20) DEFAULT 'pendente',
    card_last4      CHAR(4),
    pix_code        VARCHAR(200),
    subtotal        DECIMAL(10,2) NOT NULL,
    delivery_fee    DECIMAL(10,2) NOT NULL DEFAULT 0,
    total           DECIMAL(10,2) NOT NULL,
    eta_minutes     INT DEFAULT 40,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    paid_at         DATETIME,
    delivered_at    DATETIME,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users (id),
    INDEX idx_orders_status (status),
    INDEX idx_orders_paid_at (paid_at)    -- relatorio filtra por data
) ENGINE=InnoDB;

CREATE TABLE order_items (
    id              INT NOT NULL AUTO_INCREMENT,
    order_id        INT NOT NULL,
    product_id      INT NOT NULL,
    product_name    VARCHAR(100),
    unit_price      DECIMAL(10,2) NOT NULL,
    quantity        INT NOT NULL,
    notes           VARCHAR(200),
    PRIMARY KEY (id),
    CONSTRAINT fk_items_order FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    CONSTRAINT fk_items_product FOREIGN KEY (product_id) REFERENCES products (id),
    CONSTRAINT ck_items_qty CHECK (quantity > 0)
) ENGINE=InnoDB;

-- avaliacao, 1 por pedido (US09)
CREATE TABLE reviews (
    id          INT NOT NULL AUTO_INCREMENT,
    order_id    INT NOT NULL,
    stars       INT NOT NULL,
    comment     VARCHAR(500),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_reviews_order (order_id),
    CONSTRAINT fk_reviews_order FOREIGN KEY (order_id) REFERENCES orders (id),
    CONSTRAINT ck_reviews_stars CHECK (stars BETWEEN 1 AND 5)
) ENGINE=InnoDB;
