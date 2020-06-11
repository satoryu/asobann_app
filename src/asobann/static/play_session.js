import {el, mount, unmount, list, setStyle, setAttr} from "./redom.es.js";
import {setFeatsContext, feats} from "./feat.js";
import {
    setTableContext,
    pushComponentUpdate,
    pushNewComponent,
    pushNewKit,
    pushSyncWithMe,
    pushRemoveComponent,
    joinTable,
    pushCursorMovement
} from "./sync_table.js";
import {Menu} from "./menu.js";

function baseUrl() {
    return location.protocol + "//" + location.hostname + (location.port ? ":" + location.port : "") + "/";
}

class Component {
    constructor() {
        this.el = el(".component");
        this.image = null;

        for (const ability of feats) {
            ability.add(this);
        }
    }

    update(data, componentId, allData, context) {
        this.componentId = componentId;
        if (data.showImage) {
            if (this.image == null) {
                this.image = el("img", { draggable: false });
                this.image.ondragstart = () => {
                    return false;
                };
                mount(this.el, this.image);
            }
        }

        if (this.textEl == null) {
            this.textEl = el("span");
            mount(this.el, this.textEl);
        }
        if (data.text) {
            this.textEl.innerText = data.text;
        }
        if (data.textColor) {
            setStyle(this.textEl, { color: data.textColor });
        }

        for (const ability of feats) {
            if (ability.isEnabled(this, data)) {
                ability.update(this, data);
            }
        }

        setAttr(this.el, {
            'data-component-name': data.name,
        });

        setStyle(this.el, {
            top: parseFloat(data.top) + "px",
            left: parseFloat(data.left) + "px",
            width: parseFloat(data.width) + "px",
            height: parseFloat(data.height) + "px",
            backgroundColor: data.color,
            zIndex: this.zIndex,
        });
    }

    disappear() {
        for (const ability of feats) {
            ability.remove(this);
        }
    }

    propagate(diff) {
        pushComponentUpdate(table, this.componentId, diff, false);
    }

    propagate_volatile(diff) {
        pushComponentUpdate(table, this.componentId, diff, true);
    }
}

class Table {
    constructor() {
        console.log("new Table");
        this.el = el("div.table", { style: { top: '0px', left: '0px' } },
            this.list_el = el("div.table_list")
        );
        // this.list = list(this.list_el, Component);
        this.componentsOnTable = {};
        this.data = {};
    }

    update(data) {
        const notUpdatedComponents = Object.assign({}, this.componentsOnTable);
        setFeatsContext(getPlayerName(), isPlayerObserver(), data);

        this.data = data;

        for (const componentId in this.data.components) {
            if (!this.data.components.hasOwnProperty(componentId)) {
                continue;
            }
            const componentData = this.data.components[componentId];
            if (!this.componentsOnTable[componentId]) {
                this.componentsOnTable[componentId] = new Component();
                mount(this.list_el, this.componentsOnTable[componentId].el);
            }
            this.componentsOnTable[componentId].update(componentData, componentId, this.data.components);

            delete notUpdatedComponents[componentId]
        }

        for (const componentIdToRemove in notUpdatedComponents) {
            console.log("componentIdToRemove", componentIdToRemove);
            delete this.componentsOnTable[componentIdToRemove];
            unmount(this.list_el, notUpdatedComponents[componentIdToRemove].el);
        }
    }

    removeComponent(componentId) {
        // This is called when a component removed ON THIS BROWSER.
        // Because component removal is not directly synced but propagated as table refresh,
        // table relies on update() to detect unused / non-referenced components
        // to remove Component object and DOM object.
        // TODO: maybe it's economical to sync component removal directly...
        this.componentsOnTable[componentId].disappear();
    }
}

const sync_table_connector = {
    initializeTable: function (tableData) {
        console.log("initializeTable");
        console.log("tableData: ", tableData);
        const players = tableData.players;
        console.log("players: ", players);
        if (Object.keys(players).length === 0) {
            joinTable("host", true);  // the first player is automatically becomes host
        } else if (getPlayerName() !== "nobody") {
            joinTable(getPlayerName(), isPlayerHost());
        } else {
            setPlayerIsObserver();
        }

        table.update(tableData);
        menu.update(tableData)
    },

    update_single_component: function (componentId, diff) {
        const tableData = table.data;
        Object.assign(tableData.components[componentId], diff);
        table.update(tableData);
        menu.update(tableData);
    },

    update_whole_table: function (data) {
        table.update(data);
        menu.update(data);
    },

    updatePlayer: function (playerData) {
        if (playerData.name) {
            setPlayerIsJoined();
            setPlayerName(playerData.name);
        }
    },

    showOthersMouseMovement: function (playerName, mouseMovement) {
        const ICON_OFFSET_X = -(32 / 2);  // see "div.others_mouse_cursor .icon " in game.css
        const ICON_OFFSET_Y = -(32 / 2);
        if (playerName === getPlayerName()) {
            return;
        }
        if (!otherPlayersMouse[playerName]) {
            const e = el("div.others_mouse_cursor",
                [
                    el("div.icon"),
                    el("span", playerName),
                ]);
            mount(table.el, e);
            otherPlayersMouse[playerName] = e;
        }
        const e = otherPlayersMouse[playerName];
        const top = mouseMovement.mouseOnTableY + ICON_OFFSET_Y;
        const left = mouseMovement.mouseOnTableX + ICON_OFFSET_X;
        const className = mouseMovement.mouseButtons === 0 ? "" : "buttons_down";
        setAttr(e, { className: "others_mouse_cursor " + className });
        setStyle(e, { top: top + "px", left: left + "px", zIndex: 999999999 });
    }
};

const otherPlayersMouse = {};

function generateComponentId() {
    return 'xxxxxxxxxxxx'.replace(/[x]/g, function (c) {
        return (Math.random() * 16 | 0).toString(16);
    });
}

function addNewKit(kitData) {
    const kitName = kitData.kit.name;
    const kitId = 'xxxxxxxxxxxx'.replace(/[x]/g, function (c) {
        return (Math.random() * 16 | 0).toString(16);
    });

    const baseZIndex = getNextZIndex();
    const rect = findEmptySpace(kitData.kit.width, kitData.kit.height);
    (async () => {
        const newComponents = {};
        const componentsData = await (await fetch(encodeURI(baseUrl() + "components?kit_name=" + kitName))).json();
        for (const data of await componentsData) {
            const component = data.component;
            component.kitId = kitId;
            const componentId = generateComponentId();
            component.componentId = componentId;
            component.top = parseFloat(component.top) + rect.top;
            component.left = parseFloat(component.left) + rect.left;
            if(component.zIndex) {
                component.zIndex += baseZIndex;
            } else {
                component.zIndex = baseZIndex;
            }
            newComponents[componentId] = component;
        }
        pushNewKit({
            kit: { name: kitName, kitId: kitId },
            components: newComponents
        });
    })();
}

function removeKit(kitId) {
    const after = {};
    for (const componentId in table.data.components) {
        const cmp = table.data.components[componentId];
        if (cmp.kitId === kitId) {
            table.removeComponent(cmp.componentId);
        } else {
            after[cmp.componentId] = cmp;
        }
    }
    table.data.components = after;
    table.data.kits.splice(table.data.kits.findIndex((e) => e.kitId === kitId), 1);
    pushSyncWithMe(table.data);
}

function getNextZIndex() {
    let nextZIndex = 0;
    for (const otherId in table.data.components) {
        const other = table.data.components[otherId];
        if (nextZIndex < other.zIndex) {
            nextZIndex = other.zIndex + 1;
        }
    }
    return nextZIndex;
}

function findEmptySpace(width, height) {
    const rect = {
        top: 64,
        left: 64,
        width: width,
        height: height,
    };
    for (let i = 0; i < 10; i++) {
        let collision = false;
        rect.bottom = rect.top + rect.height;
        rect.right = rect.left + rect.width;
        for (const componentId in table.data.components) {
            const target = table.data.components[componentId];
            const targetLeft = parseFloat(target.left);
            const targetTop = parseFloat(target.top);
            const targetRight = targetLeft + parseFloat(target.width);
            const targetBottom = targetTop + parseFloat(target.height);
            if (rect.left <= targetRight &&
                targetLeft <= rect.right &&
                rect.top <= targetBottom &&
                targetTop <= rect.bottom) {
                collision = true;
                break;
            }
        }
        if (!collision) {
            break;
        }
        rect.top += 100;
    }
    return rect;
}

function placeNewComponent(newComponent, baseZIndex) {
    const rect = findEmptySpace(parseInt(newComponent.width), parseInt(newComponent.height));
    newComponent.top = rect.top + "px";
    newComponent.left = rect.left + "px";
    if (newComponent.zIndex) {
        if (baseZIndex) {
            newComponent.zIndex += baseZIndex;
        }
    } else {
        newComponent.zIndex = getNextZIndex();
    }

    if (newComponent.onAdd) {
        Function('"use strict"; return ' + newComponent.onAdd)()(newComponent);
    }
}

function addNewComponent(newComponentData) {
    newComponentData.componentId = generateComponentId();
    placeNewComponent(newComponentData);
    pushNewComponent(newComponentData);
    return false;


}

function removeHandArea() {
    for (const componentId in table.data.components) {
        const cmp = table.data.components[componentId];
        if (cmp.handArea && cmp.owner === getPlayerName()) {
            removeComponent(componentId);
            return false;
        }
    }
    return false;
}

function removeComponent(componentId) {
    table.removeComponent(componentId);
    pushRemoveComponent(componentId);
}

function getPlayerName() {
    if (sessionStorage.getItem(SESSION_STORAGE_KEY.playerName)) {
        return sessionStorage.getItem(SESSION_STORAGE_KEY.playerName);
    }
    return "nobody";
}

function setPlayerName(playerName) {
    sessionStorage.setItem(SESSION_STORAGE_KEY.playerName, playerName);
    menu.update({ playerName: playerName });
}

function isPlayerHost() {
    return sessionStorage.getItem(SESSION_STORAGE_KEY.isHost) === "true";
}

function setPlayerIsHost() {
    sessionStorage.setItem(SESSION_STORAGE_KEY.isHost, "true");
    menu.update({ isHost: true });
}

function isPlayerObserver() {
    return sessionStorage.getItem(SESSION_STORAGE_KEY.status) === "observer";
}

function setPlayerIsObserver() {
    sessionStorage.setItem(SESSION_STORAGE_KEY.status, "observer");
    menu.update({});
}

function setPlayerIsJoined() {
    sessionStorage.setItem(SESSION_STORAGE_KEY.status, "joined");
    menu.update({});
}

const tablename = location.pathname.split("/")[2];
const container = el("div.container");
mount(document.body, container);
const table = new Table();
const tableContainer = el("div.table_container", [table.el]);
mount(container, tableContainer);

const SESSION_STORAGE_KEY = {
    playerName: "asobann: " + tablename + ": playerName",
    isHost: "asobann: " + tablename + ": isHost",
    status: "asobann: " + tablename + ": status",
};


interact("div.table_container").draggable({
    listeners: {
        move(event) {
            let top = table.el.style.top === "" ? 0 : parseFloat(table.el.style.top);
            top += event.dy;
            let left = table.el.style.left === "" ? 0 : parseFloat(table.el.style.left);
            left += event.dx;
            table.el.style.top = top + "px";
            table.el.style.left = left + "px";

            tableContainer.style.backgroundPositionY = top + "px";
            tableContainer.style.backgroundPositionX = left + "px";
        },
    },
});

function isTherePlayersHandArea(playerName) {
    if (table.data.components) {
        for (const cmpId in table.data.components) {
            const cmp = table.data.components[cmpId];
            if (cmp.handArea && cmp.owner === playerName) {
                return true;
            }
        }
    }
    return false;
}

setTableContext(tablename, sync_table_connector);

const menuConnector = {
    tablename: tablename,
    getTableData: () => {
        return table.data;
    },
    fireMenuUpdate: () => {
        menu.update(table.data);
    },
    removeComponent: removeComponent,
    getPlayerName: getPlayerName,
    addNewKit: addNewKit,
    removeKit: removeKit,
    addNewComponent: addNewComponent,
    removeHandArea: removeHandArea,
    isPlayerObserver: isPlayerObserver,
    isTherePlayersHandArea: isTherePlayersHandArea,
};

const menu = new Menu(menuConnector);
mount(container, menu.el);

tableContainer.addEventListener("mousemove", (event) => {
    if (isPlayerObserver()) {
        return;
    }
    const r = tableContainer.getBoundingClientRect();
    const mouseOnTableX = event.clientX - r.left - parseFloat(table.el.style.left);
    const mouseOnTableY = event.clientY - r.top - parseFloat(table.el.style.top);
    pushCursorMovement(getPlayerName(), {
        mouseOnTableX: mouseOnTableX,
        mouseOnTableY: mouseOnTableY,
        mouseButtons: event.buttons,
    })
});