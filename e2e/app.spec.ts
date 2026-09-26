import { expect, test } from '@playwright/test'

test('主要業務フローと4画面が動作する', async ({ page }, testInfo) => {
  const errors:string[]=[]
  page.on('pageerror', e=>errors.push(e.message))
  page.on('console', message=>{if(message.type()==='error')errors.push(message.text())})
  await page.goto('/')
  await expect(page.getByRole('heading',{name:/現地確認が必要な農地/})).toBeVisible()
  await expect(page.getByText('全275筆中')).toBeVisible()
  await expect(page.getByRole('heading',{name:'2025年の衛星判定'})).toBeVisible()
  await expect(page.locator('.maplibregl-canvas')).toBeVisible()
  await expect(page.locator('.maplibregl-ctrl-attrib')).toContainText('OpenStreetMap')
  await page.screenshot({ path:`tmp/qa-dashboard-${testInfo.project.name}.png`, fullPage:true })
  await page.getByRole('button',{name:/現地確認リスト/}).first().click()
  await expect(page.getByRole('heading',{name:'現地確認リスト'})).toBeVisible()
  await expect(page.getByRole('button',{name:'CSVを出力'})).toBeEnabled()
  if(testInfo.project.name==='desktop-chromium'){
    await page.screenshot({ path:'tmp/qa-candidates.png', fullPage:true })
    await page.getByRole('button',{name:'調査試算'}).click()
    await expect(page.getByRole('heading',{name:'調査削減シナリオ'})).toBeVisible()
    await page.screenshot({ path:'tmp/qa-estimate.png', fullPage:true })
    await page.getByRole('button',{name:'判定方法'}).click()
    await expect(page.getByRole('heading',{name:'この判定について'})).toBeVisible()
    await page.screenshot({ path:'tmp/qa-method.png', fullPage:true })
  }
  expect(errors).toEqual([])
})
