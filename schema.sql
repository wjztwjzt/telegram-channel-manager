-- Telegram 频道数据统计与人员管理机器人 —— 数据库结构
-- 使用：mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS telegram_channel_manager
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE telegram_channel_manager;

-- 1. 被监控的频道
CREATE TABLE IF NOT EXISTS channels (
    id                 BIGINT       PRIMARY KEY COMMENT '频道 ID',
    access_hash        BIGINT       NULL COMMENT '访问哈希',
    username           VARCHAR(255) NULL COMMENT '公开用户名',
    title              VARCHAR(255) NULL COMMENT '频道标题',
    participants_count INT          NULL COMMENT '成员数',
    created_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='被监控的频道';

-- 2. Telegram 用户资料
CREATE TABLE IF NOT EXISTS users (
    id            BIGINT       PRIMARY KEY COMMENT '用户 ID',
    access_hash   BIGINT       NULL COMMENT '访问哈希',
    username      VARCHAR(255) NULL COMMENT '@用户名',
    first_name    VARCHAR(255) NULL COMMENT '名',
    last_name     VARCHAR(255) NULL COMMENT '姓',
    full_name     VARCHAR(255) NULL COMMENT '昵称',
    phone         VARCHAR(50)  NULL COMMENT '手机号',
    is_bot        TINYINT      NOT NULL DEFAULT 0 COMMENT '是否机器人',
    is_premium    TINYINT      NOT NULL DEFAULT 0 COMMENT '是否 Premium',
    language_code VARCHAR(20)  NULL COMMENT '语言',
    dc_id         INT          NULL COMMENT '数据中心',
    first_seen    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次发现',
    last_seen     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最近发现',
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Telegram 用户资料';

-- 3. 频道与用户的成员关系
CREATE TABLE IF NOT EXISTS channel_members (
    channel_id BIGINT       NOT NULL COMMENT '频道 ID',
    user_id    BIGINT       NOT NULL COMMENT '用户 ID',
    joined_at  DATETIME     NULL COMMENT '加入时间',
    left_at    DATETIME     NULL COMMENT '退出时间',
    status     VARCHAR(30)  NULL COMMENT '状态：member/left/kicked',
    inviter_id BIGINT       NULL COMMENT '邀请人 ID',
    source     VARCHAR(255) NULL COMMENT '来源（邀请链接/入口）',
    updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (channel_id, user_id),
    INDEX idx_joined_at (joined_at),
    INDEX idx_left_at (left_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='频道成员关系';

-- 4. 成员事件流水（JOIN / LEAVE / KICK / INVITE / JOIN_REQUEST）
CREATE TABLE IF NOT EXISTS member_events (
    id                BIGINT       NOT NULL AUTO_INCREMENT COMMENT '自增 ID',
    channel_id        BIGINT       NOT NULL COMMENT '频道 ID',
    user_id           BIGINT       NOT NULL COMMENT '用户 ID',
    event_type        VARCHAR(30)  NOT NULL COMMENT '事件类型',
    event_time        DATETIME     NOT NULL COMMENT '事件时间',
    inviter_id        BIGINT       NULL COMMENT '邀请人 ID',
    invite_link       VARCHAR(255) NULL COMMENT '邀请链接',
    telegram_event_id BIGINT       NULL COMMENT 'Telegram 管理员日志事件 ID（去重）',

    PRIMARY KEY (id),
    UNIQUE KEY uk_telegram_event (telegram_event_id),
    INDEX idx_channel_time (channel_id, event_time),
    INDEX idx_user_time (user_id, event_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成员事件流水';

-- 5. 频道消息最新快照
CREATE TABLE IF NOT EXISTS messages (
    channel_id BIGINT      NOT NULL COMMENT '频道 ID',
    message_id BIGINT      NOT NULL COMMENT '消息 ID',
    date       DATETIME    NULL COMMENT '发布时间',
    author_id  BIGINT      NULL COMMENT '作者 ID',
    text       TEXT        NULL COMMENT '文本摘要',
    views      BIGINT      NOT NULL DEFAULT 0 COMMENT '浏览',
    forwards   BIGINT      NOT NULL DEFAULT 0 COMMENT '转发',
    reactions  BIGINT      NOT NULL DEFAULT 0 COMMENT '反应',
    updated_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (channel_id, message_id),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='频道消息最新快照';

-- 6. 消息统计时间序列（按采集时间保存曲线）
CREATE TABLE IF NOT EXISTS message_stats (
    channel_id  BIGINT   NOT NULL COMMENT '频道 ID',
    message_id  BIGINT   NOT NULL COMMENT '消息 ID',
    captured_at DATETIME NOT NULL COMMENT '采集时间',
    views       BIGINT   NOT NULL DEFAULT 0 COMMENT '浏览',
    forwards    BIGINT   NOT NULL DEFAULT 0 COMMENT '转发',
    reactions   BIGINT   NOT NULL DEFAULT 0 COMMENT '反应',

    PRIMARY KEY (channel_id, message_id, captured_at),
    INDEX idx_channel_captured (channel_id, captured_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息统计时间序列';

-- 7. 邀请链接清单
CREATE TABLE IF NOT EXISTS invite_links (
    id         BIGINT       NOT NULL AUTO_INCREMENT COMMENT '自增 ID',
    channel_id BIGINT       NOT NULL COMMENT '频道 ID',
    link       VARCHAR(255) NULL COMMENT '邀请链接',
    name       VARCHAR(255) NULL COMMENT '链接备注/来源名',
    creator_id BIGINT       NULL COMMENT '创建者 ID',
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    PRIMARY KEY (id),
    INDEX idx_channel (channel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='邀请链接清单';

-- 8. 频道日报快照（每日一行）
CREATE TABLE IF NOT EXISTS daily_stats (
    date            DATE   NOT NULL COMMENT '日期',
    channel_id      BIGINT NOT NULL COMMENT '频道 ID',
    new_members     INT    NOT NULL DEFAULT 0 COMMENT '新增',
    left_members    INT    NOT NULL DEFAULT 0 COMMENT '退出',
    net_growth      INT    NOT NULL DEFAULT 0 COMMENT '净增长',
    total_views     BIGINT NOT NULL DEFAULT 0 COMMENT '总浏览',
    total_forwards  BIGINT NOT NULL DEFAULT 0 COMMENT '总转发',
    total_reactions BIGINT NOT NULL DEFAULT 0 COMMENT '总反应',
    posts           INT    NOT NULL DEFAULT 0 COMMENT '发文数',

    PRIMARY KEY (date, channel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='频道日报快照';
